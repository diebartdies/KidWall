import 'package:flutter/material.dart';
import '../api_service.dart';
import 'emergency_contacts_screen.dart'; // file kept as-is, screen title updated

const _relationships = [
  'Father',
  'Mother',
  'Uncle',
  'Aunt',
  'Grandfather',
  'Grandmother',
  'Legal Guardian',
  'Other',
];

const _shifts = ['Morning', 'Afternoon', 'Night', 'Rotating', 'Remote'];

const _countries = [
  {'name': 'United States', 'code': '+1'},
  {'name': 'Argentina', 'code': '+54'},
  {'name': 'Mexico', 'code': '+52'},
  {'name': 'Brazil', 'code': '+55'},
  {'name': 'Chile', 'code': '+56'},
  {'name': 'Colombia', 'code': '+57'},
  {'name': 'Uruguay', 'code': '+598'},
  {'name': 'Paraguay', 'code': '+595'},
  {'name': 'Peru', 'code': '+51'},
  {'name': 'Spain', 'code': '+34'},
];

class ParentProfileFormScreen extends StatefulWidget {
  final String token;
  final int parentId;

  const ParentProfileFormScreen({
    super.key,
    required this.token,
    required this.parentId,
  });

  @override
  State<ParentProfileFormScreen> createState() =>
      _ParentProfileFormScreenState();
}

class _ParentProfileFormScreenState extends State<ParentProfileFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final ApiService _api = ApiService();

  bool _loading = true;
  bool _saving = false;
  String? _error;

  String? _relationship;
  String? _shift;
  String? _country = 'United States';

  final _childrenUsingColePagoCtrl = TextEditingController();
  final _mobileCtrl = TextEditingController();
  final _countryCodeCtrl = TextEditingController(text: '+1');
  final _emailCtrl = TextEditingController();
  final _homeAddressCtrl = TextEditingController();
  final _homePostalCtrl = TextEditingController();
  final _homePhoneCtrl = TextEditingController();
  final _workNameCtrl = TextEditingController();
  final _workAddressCtrl = TextEditingController();
  final _workPhoneCtrl = TextEditingController();
  final _workHoursCtrl = TextEditingController();
  final _workplaceCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _api.setToken(widget.token);
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    try {
      final data = await _api.get('/parent/${widget.parentId}/profile');
      if (data.isNotEmpty) {
        setState(() {
          _relationship = _relationships.contains(data['relationship_to_child'])
              ? data['relationship_to_child']
              : null;
          _childrenUsingColePagoCtrl.text =
              data['children_using_colepago']?.toString() ?? '';
          _mobileCtrl.text = data['mobile_phone'] ?? '';
          _country = _countryFromProfile(data['country'], data['country_code']);
          _countryCodeCtrl.text = data['country_code'] ?? _codeForCountry(_country);
          _emailCtrl.text = data['email'] ?? '';
          _homeAddressCtrl.text = data['home_address'] ?? '';
          _homePostalCtrl.text = data['home_postal'] ?? '';
          _homePhoneCtrl.text = data['home_phone'] ?? '';
          _workNameCtrl.text = data['work_name'] ?? '';
          _workAddressCtrl.text = data['work_address'] ?? '';
          _workPhoneCtrl.text = data['work_phone'] ?? '';
          _shift = _shifts.contains(data['work_shift'])
              ? data['work_shift']
              : null;
          _workHoursCtrl.text = data['work_hours'] ?? '';
          _workplaceCtrl.text = data['workplace'] ?? '';
        });
      }
    } catch (_) {
      // No profile yet — blank form is fine
    }
    setState(() => _loading = false);
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      await _api.put('/parent/${widget.parentId}/profile', {
        'relationship_to_child': _relationship,
        'children_using_colepago': int.tryParse(
          _childrenUsingColePagoCtrl.text.trim(),
        ),
        'mobile_phone': _mobileCtrl.text.trim(),
        'country': _country,
        'country_code': _countryCodeCtrl.text.trim(),
        'email': _emailCtrl.text.trim(),
        'home_address': _homeAddressCtrl.text.trim(),
        'home_postal': _homePostalCtrl.text.trim(),
        'home_phone': _homePhoneCtrl.text.trim(),
        'work_name': _workNameCtrl.text.trim(),
        'work_address': _workAddressCtrl.text.trim(),
        'work_phone': _workPhoneCtrl.text.trim(),
        'work_shift': _shift,
        'work_hours': _workHoursCtrl.text.trim(),
        'workplace': _workplaceCtrl.text.trim(),
      });
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      setState(() => _error = 'Failed to save profile. Please try again.');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  void dispose() {
    for (final c in [
      _childrenUsingColePagoCtrl,
      _mobileCtrl,
      _countryCodeCtrl,
      _emailCtrl,
      _homeAddressCtrl,
      _homePostalCtrl,
      _homePhoneCtrl,
      _workNameCtrl,
      _workAddressCtrl,
      _workPhoneCtrl,
      _workHoursCtrl,
      _workplaceCtrl,
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Parent Information'),
        backgroundColor: const Color(0xFF3F51B5),
        foregroundColor: Colors.white,
        actions: [
          TextButton.icon(
            onPressed: _saving ? null : _save,
            icon: _saving
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Colors.white,
                    ),
                  )
                : const Icon(Icons.check, color: Colors.white),
            label: const Text('Save', style: TextStyle(color: Colors.white)),
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
                  if (_error != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: Text(
                        _error!,
                        style: const TextStyle(color: Colors.red),
                      ),
                    ),

                  _sectionHeader('Personal'),
                  _dropdownField(
                    label: 'Relationship to child',
                    value: _relationship,
                    items: _relationships,
                    onChanged: (v) => setState(() => _relationship = v),
                    required: true,
                  ),
                  const SizedBox(height: 12),
                  _textField(
                    _childrenUsingColePagoCtrl,
                    'How many children will use ColePago?',
                    keyboardType: TextInputType.number,
                    required: true,
                    validator: (v) {
                      final count = int.tryParse((v ?? '').trim());
                      if (count == null || count <= 0) {
                        return 'Enter a valid number';
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 12),
                  _dropdownField(
                    label: 'Country',
                    value: _country,
                    items: _countries.map((c) => c['name']!).toList(),
                    onChanged: (v) => setState(() {
                      _country = v;
                      _countryCodeCtrl.text = _codeForCountry(v);
                    }),
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
                          hint: '+1',
                          keyboardType: TextInputType.phone,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: _textField(
                          _mobileCtrl,
                          'Mobile number',
                          keyboardType: TextInputType.phone,
                          required: true,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  _textField(
                    _emailCtrl,
                    'Email account',
                    keyboardType: TextInputType.emailAddress,
                  ),

                  const SizedBox(height: 20),
                  _sectionHeader('Home'),
                  _textField(_homeAddressCtrl, 'Home address'),
                  const SizedBox(height: 12),
                  _textField(_homePostalCtrl, 'Postal code'),
                  const SizedBox(height: 12),
                  _textField(
                    _homePhoneCtrl,
                    'Home phone',
                    keyboardType: TextInputType.phone,
                  ),

                  const SizedBox(height: 20),
                  _sectionHeader('Work'),
                  _textField(_workNameCtrl, 'Company / employer name'),
                  const SizedBox(height: 12),
                  _textField(_workplaceCtrl, 'Workplace'),
                  const SizedBox(height: 12),
                  _textField(_workAddressCtrl, 'Work address'),
                  const SizedBox(height: 12),
                  _textField(
                    _workPhoneCtrl,
                    'Work phone',
                    keyboardType: TextInputType.phone,
                  ),
                  const SizedBox(height: 12),
                  _dropdownField(
                    label: 'Work shift',
                    value: _shift,
                    items: _shifts,
                    onChanged: (v) => setState(() => _shift = v),
                  ),
                  const SizedBox(height: 12),
                  _textField(
                    _workHoursCtrl,
                    'Working hours',
                    hint: 'e.g. 08:00 – 16:00',
                  ),

                  const SizedBox(height: 28),
                  OutlinedButton.icon(
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => EmergencyContactsScreen(
                            token: widget.token,
                            parentId: widget.parentId,
                          ),
                        ),
                      );
                    },
                    icon: const Icon(Icons.contact_phone_outlined),
                    label: const Text('Trusted Contacts'),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      side: const BorderSide(color: Color(0xFF3F51B5)),
                      foregroundColor: const Color(0xFF3F51B5),
                    ),
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
      style: const TextStyle(
        fontSize: 13,
        fontWeight: FontWeight.w700,
        color: Color(0xFF3F51B5),
        letterSpacing: 0.8,
      ),
    ),
  );

  String _codeForCountry(String? country) {
    return _countries.firstWhere(
      (c) => c['name'] == country,
      orElse: () => _countries.first,
    )['code']!;
  }

  String _countryFromProfile(dynamic country, dynamic code) {
    final countryText = country?.toString();
    if (_countries.any((c) => c['name'] == countryText)) {
      return countryText!;
    }
    final codeText = code?.toString();
    return _countries.firstWhere(
      (c) => c['code'] == codeText,
      orElse: () => _countries.first,
    )['name']!;
  }

  Widget _textField(
    TextEditingController ctrl,
    String label, {
    String? hint,
    TextInputType keyboardType = TextInputType.text,
    bool required = false,
    String? Function(String?)? validator,
  }) => TextFormField(
    controller: ctrl,
    keyboardType: keyboardType,
    decoration: InputDecoration(
      labelText: label,
      hintText: hint,
      border: const OutlineInputBorder(),
      isDense: true,
    ),
    validator:
        validator ??
        (required
            ? (v) => (v == null || v.trim().isEmpty) ? 'Required' : null
            : null),
  );

  Widget _dropdownField({
    required String label,
    required String? value,
    required List<String> items,
    required ValueChanged<String?> onChanged,
    bool required = false,
  }) => DropdownButtonFormField<String>(
    initialValue: value,
    decoration: InputDecoration(
      labelText: label,
      border: const OutlineInputBorder(),
      isDense: true,
    ),
    items: items
        .map((e) => DropdownMenuItem(value: e, child: Text(e)))
        .toList(),
    onChanged: onChanged,
    validator: required
        ? (v) => (v == null || v.isEmpty) ? 'Required' : null
        : null,
  );
}
