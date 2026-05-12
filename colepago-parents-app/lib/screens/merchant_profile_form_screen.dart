import 'package:flutter/material.dart';
import '../api_service.dart';

const _placeScopes = {
  'inside_school': 'Within school',
  'outside_school': 'Outside school',
};

const _transferTypes = ['CVU', 'CBU'];

class MerchantProfileFormScreen extends StatefulWidget {
  final String token;
  final int merchantId;

  const MerchantProfileFormScreen({
    super.key,
    required this.token,
    required this.merchantId,
  });

  @override
  State<MerchantProfileFormScreen> createState() =>
      _MerchantProfileFormScreenState();
}

class _MerchantProfileFormScreenState extends State<MerchantProfileFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final ApiService _api = ApiService();

  bool _loading = true;
  bool _saving = false;
  String? _error;

  String? _placeScope;
  String? _transferType;

  final _businessNameCtrl = TextEditingController();
  final _addressCtrl = TextEditingController();
  final _personalNameCtrl = TextEditingController();
  final _countryCodeCtrl = TextEditingController(text: '+54');
  final _mobileCtrl = TextEditingController();
  final _transferAccountCtrl = TextEditingController();
  final _transferAliasCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _api.setToken(widget.token);
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    try {
      final data = await _api.get('/merchant/${widget.merchantId}/profile');
      setState(() {
        _placeScope = _placeScopes.containsKey(data['place_scope'])
            ? data['place_scope'] as String
            : null;
        _businessNameCtrl.text = data['business_name'] ?? '';
        _addressCtrl.text = data['address'] ?? '';
        _personalNameCtrl.text = data['personal_name'] ?? '';
        _countryCodeCtrl.text = data['country_code'] ?? '+54';
        _mobileCtrl.text = data['mobile_phone'] ?? '';
        _transferType = _transferTypes.contains(data['transfer_account_type'])
            ? data['transfer_account_type'] as String
            : null;
        _transferAccountCtrl.text = data['transfer_account'] ?? '';
        _transferAliasCtrl.text = data['transfer_account_alias'] ?? '';
      });
    } catch (_) {
      // Blank form is fine for a new merchant.
    }
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _saving = true;
      _error = null;
    });

    try {
      await _api.put('/merchant/${widget.merchantId}/profile', {
        'place_scope': _placeScope,
        'business_name': _businessNameCtrl.text.trim(),
        'address': _addressCtrl.text.trim(),
        'personal_name': _personalNameCtrl.text.trim(),
        'country_code': _countryCodeCtrl.text.trim(),
        'mobile_phone': _mobileCtrl.text.trim(),
        'transfer_account_type': _transferType,
        'transfer_account': _transferAccountCtrl.text.trim(),
        'transfer_account_alias': _transferAliasCtrl.text.trim(),
      });
      if (mounted) Navigator.pop(context, true);
    } catch (_) {
      setState(() => _error = 'Failed to save merchant information.');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  void dispose() {
    for (final c in [
      _businessNameCtrl,
      _addressCtrl,
      _personalNameCtrl,
      _countryCodeCtrl,
      _mobileCtrl,
      _transferAccountCtrl,
      _transferAliasCtrl,
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Merchant Information'),
        actions: [
          TextButton.icon(
            onPressed: _saving ? null : _save,
            icon: _saving
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.check),
            label: const Text('Save'),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Form(
              key: _formKey,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  if (_error != null) ...[
                    Text(_error!, style: const TextStyle(color: Colors.red)),
                    const SizedBox(height: 12),
                  ],
                  _sectionHeader('Business'),
                  _dropdownField(
                    label: 'Place',
                    value: _placeScope,
                    items: _placeScopes,
                    onChanged: (v) => setState(() => _placeScope = v),
                    required: true,
                  ),
                  const SizedBox(height: 12),
                  _textField(
                    _businessNameCtrl,
                    'Business name',
                    required: true,
                  ),
                  const SizedBox(height: 12),
                  _textField(
                    _addressCtrl,
                    'Address if outside school',
                    required: _placeScope == 'outside_school',
                  ),
                  const SizedBox(height: 20),
                  _sectionHeader('Contact'),
                  _textField(
                    _personalNameCtrl,
                    'Personal name',
                    required: true,
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      SizedBox(
                        width: 90,
                        child: _textField(
                          _countryCodeCtrl,
                          'Code',
                          hint: '+54',
                          keyboardType: TextInputType.phone,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: _textField(
                          _mobileCtrl,
                          'Mobile phone',
                          keyboardType: TextInputType.phone,
                          required: true,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),
                  _sectionHeader('Money Transfer'),
                  DropdownButtonFormField<String>(
                    initialValue: _transferType,
                    decoration: const InputDecoration(
                      labelText: 'Account type',
                      border: OutlineInputBorder(),
                      isDense: true,
                    ),
                    items: _transferTypes
                        .map((e) => DropdownMenuItem(value: e, child: Text(e)))
                        .toList(),
                    onChanged: (v) => setState(() => _transferType = v),
                    validator: (v) =>
                        v == null || v.isEmpty ? 'Required' : null,
                  ),
                  const SizedBox(height: 12),
                  _textField(
                    _transferAccountCtrl,
                    'CVU or CBU',
                    keyboardType: TextInputType.number,
                    required: _transferAliasCtrl.text.trim().isEmpty,
                    onChanged: (_) => setState(() {}),
                  ),
                  const SizedBox(height: 12),
                  _textField(
                    _transferAliasCtrl,
                    'CVU or CBU alias',
                    required: _transferAccountCtrl.text.trim().isEmpty,
                    onChanged: (_) => setState(() {}),
                  ),
                  const SizedBox(height: 24),
                ],
              ),
            ),
    );
  }

  Widget _sectionHeader(String title) => Padding(
    padding: const EdgeInsets.only(bottom: 10),
    child: Text(
      title,
      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
    ),
  );

  Widget _textField(
    TextEditingController ctrl,
    String label, {
    String? hint,
    TextInputType keyboardType = TextInputType.text,
    bool required = false,
    ValueChanged<String>? onChanged,
  }) => TextFormField(
    controller: ctrl,
    keyboardType: keyboardType,
    onChanged: onChanged,
    decoration: InputDecoration(
      labelText: label,
      hintText: hint,
      border: const OutlineInputBorder(),
      isDense: true,
    ),
    validator: required
        ? (v) => (v == null || v.trim().isEmpty) ? 'Required' : null
        : null,
  );

  Widget _dropdownField({
    required String label,
    required String? value,
    required Map<String, String> items,
    required ValueChanged<String?> onChanged,
    bool required = false,
  }) => DropdownButtonFormField<String>(
    initialValue: value,
    decoration: InputDecoration(
      labelText: label,
      border: const OutlineInputBorder(),
      isDense: true,
    ),
    items: items.entries
        .map((e) => DropdownMenuItem(value: e.key, child: Text(e.value)))
        .toList(),
    onChanged: onChanged,
    validator: required
        ? (v) => (v == null || v.isEmpty) ? 'Required' : null
        : null,
  );
}
