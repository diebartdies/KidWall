import 'package:flutter/material.dart';
import '../api_service.dart';

class EmergencyContactsScreen extends StatefulWidget {
  final String token;
  final int parentId;

  const EmergencyContactsScreen({
    super.key,
    required this.token,
    required this.parentId,
  });

  @override
  State<EmergencyContactsScreen> createState() =>
      _EmergencyContactsScreenState();
}

class _EmergencyContactsScreenState extends State<EmergencyContactsScreen> {
  final ApiService _api = ApiService();
  List<Map<String, dynamic>> _contacts = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _api.setToken(widget.token);
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final list = await _api.getList(
        '/parent/${widget.parentId}/trusted-contacts',
      );
      setState(() {
        _contacts = list
            .map((e) => Map<String, dynamic>.from(e as Map))
            .toList();
      });
    } catch (_) {
      setState(() => _contacts = []);
    }
    setState(() => _loading = false);
  }

  Future<void> _delete(int contactId) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Remove contact?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Remove', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await _api.delete(
        '/parent/${widget.parentId}/trusted-contacts/$contactId',
      );
      _load();
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to remove contact.')),
        );
      }
    }
  }

  void _openAddForm() async {
    final added = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      builder: (_) => _AddContactSheet(api: _api, parentId: widget.parentId),
    );
    if (added == true) _load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Trusted Contacts'),
        backgroundColor: const Color(0xFF3F51B5),
        foregroundColor: Colors.white,
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _openAddForm,
        backgroundColor: const Color(0xFF3F51B5),
        foregroundColor: Colors.white,
        child: const Icon(Icons.person_add),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _contacts.isEmpty
          ? Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(
                    Icons.contact_phone_outlined,
                    size: 64,
                    color: Colors.grey,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'No trusted contacts yet',
                    style: Theme.of(
                      context,
                    ).textTheme.bodyLarge?.copyWith(color: Colors.grey),
                  ),
                  const SizedBox(height: 8),
                  TextButton.icon(
                    onPressed: _openAddForm,
                    icon: const Icon(Icons.add),
                    label: const Text('Add contact'),
                  ),
                ],
              ),
            )
          : ListView.separated(
              padding: const EdgeInsets.all(12),
              itemCount: _contacts.length,
              // ignore: unnecessary_underscores
              separatorBuilder: (_, __) => const Divider(height: 1),
              itemBuilder: (_, i) {
                final c = _contacts[i];
                final name = '${c['name'] ?? ''} ${c['surname'] ?? ''}'.trim();
                final relation = c['relation'] ?? '';
                final mobile = '${c['country_code'] ?? ''} ${c['mobile'] ?? ''}'
                    .trim();
                return ListTile(
                  leading: const CircleAvatar(
                    backgroundColor: Color(0xFFE8EAF6),
                    child: Icon(Icons.person, color: Color(0xFF3F51B5)),
                  ),
                  title: Text(name.isNotEmpty ? name : 'Unnamed'),
                  subtitle: Text(
                    [relation, mobile].where((s) => s.isNotEmpty).join(' · '),
                  ),
                  trailing: IconButton(
                    icon: const Icon(Icons.delete_outline, color: Colors.red),
                    onPressed: () => _delete(c['id'] as int),
                  ),
                );
              },
            ),
    );
  }
}

class _AddContactSheet extends StatefulWidget {
  final ApiService api;
  final int parentId;

  const _AddContactSheet({required this.api, required this.parentId});

  @override
  State<_AddContactSheet> createState() => _AddContactSheetState();
}

class _AddContactSheetState extends State<_AddContactSheet> {
  final _formKey = GlobalKey<FormState>();
  bool _saving = false;

  final _nameCtrl = TextEditingController();
  final _surnameCtrl = TextEditingController();
  final _relationCtrl = TextEditingController();
  final _mobileCtrl = TextEditingController();
  final _countryCtrl = TextEditingController(text: '+1');
  final _homePhoneCtrl = TextEditingController();
  final _workPhoneCtrl = TextEditingController();
  final _addressCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();

  @override
  void dispose() {
    for (final c in [
      _nameCtrl,
      _surnameCtrl,
      _relationCtrl,
      _mobileCtrl,
      _countryCtrl,
      _homePhoneCtrl,
      _workPhoneCtrl,
      _addressCtrl,
      _emailCtrl,
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);
    try {
      await widget.api.post('/parent/${widget.parentId}/trusted-contacts', {
        'name': _nameCtrl.text.trim(),
        'surname': _surnameCtrl.text.trim(),
        'relation': _relationCtrl.text.trim(),
        'mobile': _mobileCtrl.text.trim(),
        'country_code': _countryCtrl.text.trim(),
        'home_phone': _homePhoneCtrl.text.trim(),
        'work_phone': _workPhoneCtrl.text.trim(),
        'address': _addressCtrl.text.trim(),
        'email': _emailCtrl.text.trim(),
      });
      if (mounted) Navigator.pop(context, true);
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('Failed to add contact.')));
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
      ),
      child: Form(
        key: _formKey,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  const Expanded(
                    child: Text(
                      'Add Trusted Contact',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: _field(_nameCtrl, 'First name', required: true),
                  ),
                  const SizedBox(width: 8),
                  Expanded(child: _field(_surnameCtrl, 'Last name')),
                ],
              ),
              const SizedBox(height: 10),
              _field(_relationCtrl, 'Relationship (e.g. Aunt)', required: true),
              const SizedBox(height: 10),
              Row(
                children: [
                  SizedBox(
                    width: 85,
                    child: _field(
                      _countryCtrl,
                      'Code',
                      keyboardType: TextInputType.phone,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: _field(
                      _mobileCtrl,
                      'Mobile',
                      keyboardType: TextInputType.phone,
                      required: true,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              _field(
                _homePhoneCtrl,
                'Home phone',
                keyboardType: TextInputType.phone,
              ),
              const SizedBox(height: 10),
              _field(
                _workPhoneCtrl,
                'Work phone',
                keyboardType: TextInputType.phone,
              ),
              const SizedBox(height: 10),
              _field(_addressCtrl, 'Address'),
              const SizedBox(height: 10),
              _field(
                _emailCtrl,
                'Email',
                keyboardType: TextInputType.emailAddress,
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _saving ? null : _save,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF3F51B5),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                child: _saving
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Text('Add Contact'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _field(
    TextEditingController ctrl,
    String label, {
    TextInputType keyboardType = TextInputType.text,
    bool required = false,
  }) => TextFormField(
    controller: ctrl,
    keyboardType: keyboardType,
    decoration: InputDecoration(
      labelText: label,
      border: const OutlineInputBorder(),
      isDense: true,
    ),
    validator: required
        ? (v) => (v == null || v.trim().isEmpty) ? 'Required' : null
        : null,
  );
}
