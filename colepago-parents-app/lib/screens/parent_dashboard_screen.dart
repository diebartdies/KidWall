import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import 'fund_wallet_screen.dart';
import 'add_child_screen.dart';
import 'parent_profile_form_screen.dart';
import '../api_service.dart';

class ParentDashboardScreen extends StatefulWidget {
  final String token;
  final int parentId;
  const ParentDashboardScreen({
    super.key,
    required this.token,
    required this.parentId,
  });

  @override
  State<ParentDashboardScreen> createState() => _ParentDashboardScreenState();
}

class _ParentDashboardScreenState extends State<ParentDashboardScreen> {
  List<Map<String, dynamic>> children = [];
  List<Map<String, dynamic>> childEconomy = [];
  Map<String, int> walletBuckets = {};
  List<Map<String, dynamic>> transactions = [];
  int? selectedChildId;
  double parentBalance = 0;
  double childrenBalance = 0;
  String parentPhone = '';
  bool loading = true;
  final ApiService _apiService = ApiService();

  @override
  void initState() {
    super.initState();
    _apiService.setToken(widget.token);
    _fetchDashboardData();
  }

  Future<void> _fetchDashboardData() async {
    setState(() {
      loading = true;
    });
    try {
      final fetchedChildren = await _apiService.getChildren(widget.parentId);
      final economy = await _apiService.getParentDashboardEconomy(
        widget.parentId,
      );
      final summary = await _apiService.get(
        '/parent/${widget.parentId}/wallet_summary',
      );
      final profile = await _apiService.get(
        '/parent/${widget.parentId}/profile',
      );
      Map<String, int> fetchedWalletBuckets = {};
      List<Map<String, dynamic>> fetchedTransactions = [];
      int? firstChildId = fetchedChildren.isNotEmpty
          ? fetchedChildren.first['id']
          : null;
      if (firstChildId != null) {
        fetchedWalletBuckets = await _apiService.getWalletBuckets(
          widget.parentId,
        );
        fetchedTransactions = (await _apiService.getTransactions(
          firstChildId,
        )).cast<Map<String, dynamic>>();
      }
      final fetchedParentPhone = _normalizedDialNumber(
        profile['mobile_phone'],
        profile['country_code'],
      );
      if (fetchedParentPhone.isNotEmpty) {
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(_parentPhoneCacheKey, fetchedParentPhone);
      }
      setState(() {
        children = fetchedChildren;
        childEconomy = (economy['children'] as List? ?? [])
            .whereType<Map<String, dynamic>>()
            .toList();
        selectedChildId = firstChildId;
        walletBuckets = fetchedWalletBuckets;
        transactions = fetchedTransactions;
        parentBalance = _asDouble(summary['parent_balance']);
        childrenBalance = _asDouble(summary['children_balance']);
        parentPhone = fetchedParentPhone;
        loading = false;
      });
    } catch (e) {
      final cachedParentPhone = await _cachedParentPhone();
      setState(() {
        children = [];
        childEconomy = [];
        selectedChildId = null;
        walletBuckets = {};
        transactions = [];
        parentBalance = 0;
        childrenBalance = 0;
        parentPhone = cachedParentPhone;
        loading = false;
      });
      // Optionally show error
      // ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to load dashboard data')));
    }
  }

  @override
  Widget build(BuildContext context) {
    // Ensure c['id'] is unique for each child (debug only)
    assert(
      children.map((c) => c['id'] as int).toSet().length == children.length,
      'Each child id must be unique.',
    );
    return Scaffold(
      appBar: AppBar(
        title: const Text('Parent Dashboard'),
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.menu),
            onSelected: _handleDashboardAction,
            itemBuilder: (context) => const [
              PopupMenuItem(
                value: 'parent',
                child: ListTile(
                  leading: Icon(Icons.settings),
                  title: Text('Modify parent information'),
                ),
              ),
              PopupMenuItem(
                value: 'children',
                child: ListTile(
                  leading: Icon(Icons.child_care),
                  title: Text('Modify kid information'),
                ),
              ),
              PopupMenuItem(
                value: 'money',
                child: ListTile(
                  leading: Icon(Icons.account_balance_wallet),
                  title: Text('Load or apply money'),
                ),
              ),
              PopupMenuItem(
                value: 'call',
                child: ListTile(
                  leading: Icon(Icons.phone),
                  title: Text('Call parent phone'),
                ),
              ),
            ],
          ),
        ],
      ),
      drawer: Drawer(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            const DrawerHeader(
              decoration: BoxDecoration(color: Colors.blueAccent),
              child: Text(
                'Menu',
                style: TextStyle(color: Colors.white, fontSize: 24),
              ),
            ),
            ListTile(
              leading: const Icon(Icons.settings),
              title: const Text('Parent Config'),
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => ParentProfileFormScreen(
                      token: widget.token,
                      parentId: widget.parentId,
                    ),
                  ),
                );
              },
            ),
            ListTile(
              leading: const Icon(Icons.child_care),
              title: const Text('Manage Children'),
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => AddChildScreen(
                      token: widget.token,
                      parentId: widget.parentId,
                    ),
                  ),
                );
              },
            ),
            ListTile(
              leading: const Icon(Icons.account_balance_wallet),
              title: const Text('Add Credit'),
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => FundWalletScreen(
                      token: widget.token,
                      parentId: widget.parentId,
                    ),
                  ),
                ).then((_) => _fetchDashboardData());
              },
            ),
            ListTile(
              leading: const Icon(Icons.phone),
              title: const Text('Call parent phone'),
              onTap: () {
                Navigator.pop(context);
                _callParentPhone();
              },
            ),
          ],
        ),
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Wallet buckets
                  Row(
                    children: [
                      Expanded(
                        child: _BalanceCard(
                          label: 'Parent Wallet',
                          amount: parentBalance,
                          icon: Icons.account_balance_wallet,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: _BalanceCard(
                          label: 'Applied to Children',
                          amount: childrenBalance,
                          icon: Icons.child_care,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton.icon(
                          icon: const Icon(Icons.add_card),
                          label: const Text('Load Money'),
                          onPressed: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => FundWalletScreen(
                                  token: widget.token,
                                  parentId: widget.parentId,
                                  initialMode: FundWalletMode.general,
                                ),
                              ),
                            ).then((_) => _fetchDashboardData());
                          },
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: OutlinedButton.icon(
                          icon: const Icon(Icons.tune),
                          label: const Text('Apply to Child'),
                          onPressed: children.isEmpty
                              ? null
                              : () {
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (_) => FundWalletScreen(
                                        token: widget.token,
                                        parentId: widget.parentId,
                                        initialMode: FundWalletMode.child,
                                        initialChildId: selectedChildId,
                                      ),
                                    ),
                                  ).then((_) => _fetchDashboardData());
                                },
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  Text(
                    'Kids Economic Situation',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 8),
                  if (childEconomy.isEmpty)
                    const Text('No kid economy data yet.')
                  else
                    SizedBox(
                      height: 245,
                      child: ListView.separated(
                        scrollDirection: Axis.horizontal,
                        itemCount: childEconomy.length,
                        separatorBuilder: (_, _) => const SizedBox(width: 12),
                        itemBuilder: (context, index) =>
                            _KidEconomyCard(data: childEconomy[index]),
                      ),
                    ),
                  const SizedBox(height: 24),
                  Text(
                    'Wallet Balance per Bucket',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 8),
                  SizedBox(
                    height: 80,
                    child: ListView(
                      scrollDirection: Axis.horizontal,
                      children: walletBuckets.entries
                          .map(
                            (e) => Card(
                              margin: const EdgeInsets.symmetric(horizontal: 8),
                              child: Container(
                                width: 120,
                                padding: const EdgeInsets.all(12),
                                child: Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Text(
                                      e.key,
                                      style: const TextStyle(
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                    const SizedBox(height: 8),
                                    Text(
                                      '${e.value} MXN',
                                      style: const TextStyle(fontSize: 18),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          )
                          .toList(),
                    ),
                  ),
                  const SizedBox(height: 24),
                  // Children dropdown
                  if (children.isEmpty) ...[
                    const SizedBox(height: 24),
                    Center(
                      child: Column(
                        children: [
                          Text(
                            'No children found. Please add at least one child to view wallet and transactions.',
                            style: TextStyle(color: Colors.red, fontSize: 16),
                            textAlign: TextAlign.center,
                          ),
                          const SizedBox(height: 16),
                          ElevatedButton.icon(
                            icon: const Icon(Icons.child_care),
                            label: const Text('Add Child'),
                            onPressed: () {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (context) => AddChildScreen(
                                    token: widget.token,
                                    parentId: widget.parentId,
                                  ),
                                ),
                              );
                            },
                          ),
                        ],
                      ),
                    ),
                  ] else ...[
                    Row(
                      children: [
                        const Text('Child: '),
                        DropdownButton<int>(
                          value: selectedChildId,
                          items: children
                              .map(
                                (c) => DropdownMenuItem(
                                  value: c['id'] as int,
                                  child: Text(c['name']),
                                ),
                              )
                              .toList(),
                          onChanged: (id) async {
                            setState(() {
                              selectedChildId = id;
                              loading = true;
                            });
                            try {
                              final fetchedTransactions = id != null
                                  ? (await _apiService.getTransactions(
                                      id,
                                    )).cast<Map<String, dynamic>>()
                                  : <Map<String, dynamic>>[];
                              setState(() {
                                transactions = fetchedTransactions;
                                loading = false;
                              });
                            } catch (e) {
                              setState(() {
                                transactions = [];
                                loading = false;
                              });
                            }
                          },
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    // Recent transactions
                    Text(
                      'Recent Transactions',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 8),
                    Expanded(
                      child: ListView(
                        children: transactions
                            .where((t) => t['childId'] == selectedChildId)
                            .map(
                              (t) => ListTile(
                                leading: Icon(
                                  t['amount'] > 0 ? Icons.add : Icons.remove,
                                  color: t['amount'] > 0
                                      ? Colors.green
                                      : Colors.red,
                                ),
                                title: Text(t['desc']),
                                subtitle: Text(t['date']),
                                trailing: Text('${t['amount']} MXN'),
                              ),
                            )
                            .toList(),
                      ),
                    ),
                  ],
                ],
              ),
            ),
    );
  }

  double _asDouble(dynamic value) {
    if (value is num) return value.toDouble();
    return double.tryParse(value?.toString() ?? '') ?? 0;
  }

  String get _parentPhoneCacheKey => 'parentPhone:${widget.parentId}';

  Future<String> _cachedParentPhone() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_parentPhoneCacheKey) ?? '';
  }

  String _normalizedDialNumber(dynamic number, dynamic countryCode) {
    final raw = (number ?? '').toString().trim();
    if (raw.isEmpty) return '';
    if (raw.startsWith('+')) return '+${raw.replaceAll(RegExp(r'\D'), '')}';
    final digits = raw.replaceAll(RegExp(r'\D'), '');
    final ccDigits = (countryCode ?? '').toString().replaceAll(
      RegExp(r'\D'),
      '',
    );
    if (ccDigits.isNotEmpty && ccDigits.endsWith(digits)) return '+$ccDigits';
    return ccDigits.isNotEmpty ? '+$ccDigits$digits' : digits;
  }

  Future<void> _callParentPhone() async {
    if (parentPhone.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No parent mobile phone is loaded.')),
      );
      return;
    }
    final uri = Uri(scheme: 'tel', path: parentPhone);
    if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not open dialer for $parentPhone.')),
      );
    }
  }

  void _handleDashboardAction(String action) {
    if (action == 'parent') {
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => ParentProfileFormScreen(
            token: widget.token,
            parentId: widget.parentId,
          ),
        ),
      ).then((_) => _fetchDashboardData());
      return;
    }
    if (action == 'children') {
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) =>
              AddChildScreen(token: widget.token, parentId: widget.parentId),
        ),
      ).then((_) => _fetchDashboardData());
      return;
    }
    if (action == 'money') {
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => FundWalletScreen(
            token: widget.token,
            parentId: widget.parentId,
            initialMode: children.isEmpty
                ? FundWalletMode.general
                : FundWalletMode.child,
            initialChildId: selectedChildId,
          ),
        ),
      ).then((_) => _fetchDashboardData());
      return;
    }
    if (action == 'call') {
      _callParentPhone();
    }
  }
}

class _BalanceCard extends StatelessWidget {
  final String label;
  final double amount;
  final IconData icon;

  const _BalanceCard({
    required this.label,
    required this.amount,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          children: [
            Icon(icon, color: Colors.blueAccent),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(label, style: Theme.of(context).textTheme.labelMedium),
                  const SizedBox(height: 4),
                  Text(
                    amount.toStringAsFixed(2),
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _KidEconomyCard extends StatelessWidget {
  final Map<String, dynamic> data;

  const _KidEconomyCard({required this.data});

  @override
  Widget build(BuildContext context) {
    final buckets = (data['buckets'] as List? ?? [])
        .whereType<Map<String, dynamic>>()
        .toList();
    final affected = (data['affected_buckets'] as List? ?? [])
        .map((item) => item.toString())
        .toList();

    return SizedBox(
      width: 310,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.child_care, color: Colors.blueAccent),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      data['name']?.toString() ?? 'Kid',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ),
                  if (affected.isNotEmpty)
                    const Icon(Icons.warning_amber, color: Colors.orange),
                ],
              ),
              const SizedBox(height: 10),
              Wrap(
                spacing: 10,
                runSpacing: 6,
                children: [
                  _metric('Remaining', data['total_remaining']),
                  _metric('7d spend', data['spend_7_days']),
                  _metric('Daily rate', data['daily_spend_rate']),
                  Text(
                    'Days left: ${data['estimated_days_left'] ?? 'n/a'}',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Expanded(
                child: ListView(
                  children: buckets.map((bucket) {
                    final pct = _asDouble(bucket['pct_used']).clamp(0, 100);
                    final warning = bucket['status'] == 'warning';
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Text(bucket['name']?.toString() ?? ''),
                              ),
                              Text(
                                _asDouble(
                                  bucket['remaining'],
                                ).toStringAsFixed(2),
                              ),
                            ],
                          ),
                          LinearProgressIndicator(
                            value: pct / 100,
                            color: warning ? Colors.orange : Colors.blueAccent,
                            backgroundColor: Colors.black12,
                          ),
                        ],
                      ),
                    );
                  }).toList(),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _metric(String label, dynamic value) {
    return Text('$label: ${_asDouble(value).toStringAsFixed(2)}');
  }

  double _asDouble(dynamic value) {
    if (value is num) return value.toDouble();
    return double.tryParse(value?.toString() ?? '') ?? 0;
  }
}
