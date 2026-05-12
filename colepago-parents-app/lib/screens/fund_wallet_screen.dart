import 'package:flutter/material.dart';

import '../api_service.dart';

enum FundWalletMode { general, child }

class FundWalletScreen extends StatefulWidget {
  final String token;
  final int parentId;
  final FundWalletMode initialMode;
  final int? initialChildId;

  const FundWalletScreen({
    super.key,
    required this.token,
    required this.parentId,
    this.initialMode = FundWalletMode.general,
    this.initialChildId,
  });

  @override
  State<FundWalletScreen> createState() => _FundWalletScreenState();
}

class _FundWalletScreenState extends State<FundWalletScreen> {
  static const _bucketNames = [
    'Lunch / Snacks',
    'Books',
    'Fotocopies',
    'Transport',
    'General',
  ];

  final _formKey = GlobalKey<FormState>();
  final _amountCtrl = TextEditingController();
  final _generalThresholdCtrl = TextEditingController(text: '80');
  final Map<String, TextEditingController> _bucketCtrls = {
    for (final name in _bucketNames) name: TextEditingController(),
  };
  final Map<String, TextEditingController> _thresholdCtrls = {
    for (final name in _bucketNames) name: TextEditingController(),
  };

  late final ApiService _api;
  late FundWalletMode _mode;
  String _fundingSource = 'new_money';
  String _paymentMethod = 'bank_transfer';
  int? _selectedChildId;
  bool _loading = true;
  bool _saving = false;
  bool _savingThresholds = false;
  String? _message;
  String? _error;
  List<Map<String, dynamic>> _children = [];

  @override
  void initState() {
    super.initState();
    _api = ApiService()..setToken(widget.token);
    _mode = widget.initialMode;
    _selectedChildId = widget.initialChildId;
    _load();
  }

  @override
  void dispose() {
    _amountCtrl.dispose();
    _generalThresholdCtrl.dispose();
    for (final ctrl in _bucketCtrls.values) {
      ctrl.dispose();
    }
    for (final ctrl in _thresholdCtrls.values) {
      ctrl.dispose();
    }
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final children = await _api.getChildren(widget.parentId);
      setState(() {
        _children = children;
        _selectedChildId ??= children.isNotEmpty
            ? children.first['id'] as int
            : null;
        _loading = false;
      });
      if (_selectedChildId != null) {
        await _loadThresholds(_selectedChildId!);
      }
    } catch (_) {
      setState(() {
        _children = [];
        _loading = false;
      });
    }
  }

  Future<void> _loadThresholds(int childId) async {
    try {
      final buckets = await _api.getChildWalletBuckets(childId);
      final thresholds = <int>[];
      for (final bucket in buckets) {
        final name = bucket['name']?.toString();
        final value = int.tryParse(
          bucket['alert_threshold_pct']?.toString() ?? '',
        );
        if (name != null &&
            value != null &&
            _thresholdCtrls.containsKey(name)) {
          _thresholdCtrls[name]!.text = value.toString();
          thresholds.add(value);
        }
      }
      if (thresholds.isNotEmpty && thresholds.toSet().length == 1) {
        _generalThresholdCtrl.text = thresholds.first.toString();
      }
      if (mounted) setState(() {});
    } catch (_) {
      // New buckets can still receive thresholds during allocation.
    }
  }

  int _thresholdValue(TextEditingController ctrl, int fallback) {
    final value = int.tryParse(ctrl.text.trim());
    if (value == null) return fallback;
    return value.clamp(1, 100).toInt();
  }

  List<Map<String, dynamic>> _thresholdPayload() {
    final fallback = _thresholdValue(_generalThresholdCtrl, 80);
    return _thresholdCtrls.entries
        .map(
          (entry) => {
            'name': entry.key,
            'alert_threshold_pct': _thresholdValue(entry.value, fallback),
          },
        )
        .toList();
  }

  Future<void> _saveThresholds() async {
    final childId = _selectedChildId;
    if (childId == null) {
      setState(() => _error = 'Select a child');
      return;
    }
    setState(() {
      _savingThresholds = true;
      _message = null;
      _error = null;
    });
    try {
      await _api.updateChildBucketThresholds(
        parentId: widget.parentId,
        childId: childId,
        defaultThresholdPct: _thresholdValue(_generalThresholdCtrl, 80),
        buckets: _thresholdPayload(),
      );
      setState(() => _message = 'Bucket warning thresholds saved.');
    } catch (e) {
      setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _savingThresholds = false);
    }
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _saving = true;
      _message = null;
      _error = null;
    });

    final amount = double.parse(_amountCtrl.text.trim());
    try {
      if (_mode == FundWalletMode.general) {
        await _api.fundWallet(
          parentId: widget.parentId,
          amount: amount,
          paymentMethod: _paymentMethod,
        );
        setState(() => _message = 'Money loaded to the parent wallet.');
        return;
      }

      final childId = _selectedChildId;
      if (childId == null) {
        throw Exception('Select a child');
      }

      final buckets = _bucketCtrls.entries
          .map(
            (entry) => {
              'name': entry.key,
              'amount': double.tryParse(entry.value.text.trim()) ?? 0.0,
              'alert_threshold_pct': _thresholdValue(
                _thresholdCtrls[entry.key]!,
                _thresholdValue(_generalThresholdCtrl, 80),
              ),
            },
          )
          .where((entry) => (entry['amount'] as double) > 0)
          .toList();

      final bucketTotal = buckets.fold<double>(
        0,
        (sum, entry) => sum + (entry['amount'] as double),
      );
      if ((bucketTotal - amount).abs() > 0.01) {
        throw Exception('Bucket amounts must equal the amount to apply.');
      }

      if (_fundingSource == 'new_money') {
        await _api.fundWallet(
          parentId: widget.parentId,
          amount: amount,
          paymentMethod: _paymentMethod,
        );
      }
      await _api.allocateWalletToChild(
        parentId: widget.parentId,
        childId: childId,
        amount: amount,
        buckets: buckets,
      );
      setState(() => _message = 'Money applied to child buckets.');
    } catch (e) {
      setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Load Money')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Form(
              key: _formKey,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  SegmentedButton<FundWalletMode>(
                    segments: const [
                      ButtonSegment(
                        value: FundWalletMode.general,
                        label: Text('General'),
                        icon: Icon(Icons.account_balance_wallet),
                      ),
                      ButtonSegment(
                        value: FundWalletMode.child,
                        label: Text('Child'),
                        icon: Icon(Icons.child_care),
                      ),
                    ],
                    selected: {_mode},
                    onSelectionChanged: (value) =>
                        setState(() => _mode = value.first),
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _amountCtrl,
                    keyboardType: const TextInputType.numberWithOptions(
                      decimal: true,
                    ),
                    decoration: const InputDecoration(
                      labelText: 'Amount',
                      prefixIcon: Icon(Icons.attach_money),
                      border: OutlineInputBorder(),
                    ),
                    validator: (v) {
                      final value = double.tryParse((v ?? '').trim());
                      if (value == null || value <= 0) {
                        return 'Enter a valid amount';
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 16),
                  if (_mode == FundWalletMode.child) ...[
                    DropdownButtonFormField<int>(
                      initialValue: _selectedChildId,
                      decoration: const InputDecoration(
                        labelText: 'Child',
                        border: OutlineInputBorder(),
                      ),
                      items: _children
                          .map(
                            (child) => DropdownMenuItem<int>(
                              value: child['id'] as int,
                              child: Text(child['name']?.toString() ?? 'Child'),
                            ),
                          )
                          .toList(),
                      onChanged: (value) {
                        setState(() => _selectedChildId = value);
                        if (value != null) {
                          _loadThresholds(value);
                        }
                      },
                      validator: (_) =>
                          _children.isEmpty ? 'Add a child first' : null,
                    ),
                    const SizedBox(height: 16),
                    DropdownButtonFormField<String>(
                      initialValue: _fundingSource,
                      decoration: const InputDecoration(
                        labelText: 'Source',
                        border: OutlineInputBorder(),
                      ),
                      items: const [
                        DropdownMenuItem(
                          value: 'new_money',
                          child: Text('Load new money and apply now'),
                        ),
                        DropdownMenuItem(
                          value: 'parent_balance',
                          child: Text('Use existing parent wallet balance'),
                        ),
                      ],
                      onChanged: (value) =>
                          setState(() => _fundingSource = value ?? 'new_money'),
                    ),
                    const SizedBox(height: 16),
                  ],
                  if (_mode == FundWalletMode.general ||
                      (_mode == FundWalletMode.child &&
                          _fundingSource == 'new_money')) ...[
                    DropdownButtonFormField<String>(
                      initialValue: _paymentMethod,
                      decoration: const InputDecoration(
                        labelText: 'Payment method',
                        border: OutlineInputBorder(),
                      ),
                      items: const [
                        DropdownMenuItem(
                          value: 'bank_transfer',
                          child: Text('Manual bank transfer'),
                        ),
                        DropdownMenuItem(
                          value: 'mercadopago',
                          child: Text('Mercado Pago'),
                        ),
                        DropdownMenuItem(
                          value: 'stripe_card',
                          child: Text('Stripe card'),
                        ),
                      ],
                      onChanged: (value) => setState(
                        () => _paymentMethod = value ?? 'bank_transfer',
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],
                  if (_mode == FundWalletMode.child) ...[
                    Text(
                      'Warning Thresholds',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 8),
                    TextFormField(
                      controller: _generalThresholdCtrl,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                        labelText: 'General warning threshold %',
                        helperText:
                            'Parent is warned when used money reaches this percent.',
                        border: OutlineInputBorder(),
                      ),
                    ),
                    const SizedBox(height: 12),
                    ..._thresholdCtrls.entries.map(
                      (entry) => Padding(
                        padding: const EdgeInsets.only(bottom: 10),
                        child: TextFormField(
                          controller: entry.value,
                          keyboardType: TextInputType.number,
                          decoration: InputDecoration(
                            labelText: '${entry.key} warning %',
                            border: const OutlineInputBorder(),
                          ),
                        ),
                      ),
                    ),
                    OutlinedButton.icon(
                      icon: _savingThresholds
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.notifications_active),
                      label: const Text('Save Warning Thresholds'),
                      onPressed: _savingThresholds ? null : _saveThresholds,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'Buckets',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 8),
                    ..._bucketCtrls.entries.map(
                      (entry) => Padding(
                        padding: const EdgeInsets.only(bottom: 10),
                        child: TextFormField(
                          controller: entry.value,
                          keyboardType: const TextInputType.numberWithOptions(
                            decimal: true,
                          ),
                          decoration: InputDecoration(
                            labelText: entry.key,
                            border: const OutlineInputBorder(),
                          ),
                        ),
                      ),
                    ),
                  ],
                  if (_error != null) ...[
                    const SizedBox(height: 8),
                    Text(_error!, style: const TextStyle(color: Colors.red)),
                  ],
                  if (_message != null) ...[
                    const SizedBox(height: 8),
                    Text(
                      _message!,
                      style: const TextStyle(color: Colors.green),
                    ),
                  ],
                  const SizedBox(height: 20),
                  ElevatedButton.icon(
                    icon: _saving
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.check),
                    label: Text(
                      _mode == FundWalletMode.general
                          ? 'Load Money'
                          : 'Apply Money',
                    ),
                    onPressed: _saving ? null : _submit,
                  ),
                ],
              ),
            ),
    );
  }
}
