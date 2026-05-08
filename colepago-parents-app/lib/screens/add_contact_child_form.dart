import 'package:flutter/material.dart';

class AddContactChildForm extends StatefulWidget {
  final bool isEditing;
  final Map<String, dynamic>? initialData;
  final void Function(Map<String, dynamic>) onSave;

  const AddContactChildForm({
    super.key,
    this.isEditing = false,
    this.initialData,
    required this.onSave,
  });

  @override
  State<AddContactChildForm> createState() => _AddContactChildFormState();
}

class _AddContactChildFormState extends State<AddContactChildForm> {
  final _formKey = GlobalKey<FormState>();

  // Parent fields
  final _parentNameController = TextEditingController();
  final _parentSurnameController = TextEditingController();
  final _parentAddressController = TextEditingController();
  final _parentPostalController = TextEditingController();
  final _parentHomePhoneController = TextEditingController();
  final _parentWorkPhoneController = TextEditingController();
  final _parentMobileController = TextEditingController();
  final _parentEmailController = TextEditingController();
  final _parentWorkplaceController = TextEditingController();
  String _parentCountryCode = '+1';

  // Child fields
  final _childNameController = TextEditingController();
  final _childDobController = TextEditingController();
  final _childGradeController = TextEditingController();
  final _childShiftController = TextEditingController();
  final _childSchoolNameController = TextEditingController();
  final _childSchoolAddressController = TextEditingController();
  final _childSchoolPostalController = TextEditingController();

  // Double escolarity fields
  bool _doubleLanguage = false;
  List<String> _selectedLanguages = ['English'];
  List<String> _selectedShifts = ['Morning'];
  final List<String> _languageOptions = [
    'English',
    'German',
    'Spanish',
    'French',
  ];
  final List<String> _shiftOptions = ['Morning', 'Afternoon'];

  // Emergency contacts
  List<Map<String, dynamic>> _emergencyContacts = [];

  @override
  void dispose() {
    _parentNameController.dispose();
    _parentSurnameController.dispose();
    _parentAddressController.dispose();
    _parentPostalController.dispose();
    _parentHomePhoneController.dispose();
    _parentWorkPhoneController.dispose();
    _parentMobileController.dispose();
    _parentEmailController.dispose();
    _parentWorkplaceController.dispose();
    _childNameController.dispose();
    _childDobController.dispose();
    _childGradeController.dispose();
    _childShiftController.dispose();
    _childSchoolNameController.dispose();
    _childSchoolAddressController.dispose();
    _childSchoolPostalController.dispose();
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    if (widget.initialData != null) {
      final d = widget.initialData!;
      _parentNameController.text = d['parent_name'] ?? '';
      _parentSurnameController.text = d['parent_surname'] ?? '';
      _parentAddressController.text = d['parent_address'] ?? '';
      _parentPostalController.text = d['parent_postal'] ?? '';
      _parentHomePhoneController.text = d['parent_home_phone'] ?? '';
      _parentWorkPhoneController.text = d['parent_work_phone'] ?? '';
      _parentMobileController.text = d['parent_mobile'] ?? '';
      _parentEmailController.text = d['parent_email'] ?? '';
      _parentWorkplaceController.text = d['parent_workplace'] ?? '';
      _parentCountryCode = d['parent_country_code'] ?? '+1';
      _childNameController.text = d['child_name'] ?? '';
      _childDobController.text = d['child_dob'] ?? '';
      _childGradeController.text = d['child_grade'] ?? '';
      _childShiftController.text = d['child_shift'] ?? '';
      _childSchoolNameController.text = d['child_school_name'] ?? '';
      _childSchoolAddressController.text = d['child_school_address'] ?? '';
      _childSchoolPostalController.text = d['child_school_postal'] ?? '';
      _emergencyContacts = List<Map<String, dynamic>>.from(
        d['emergency_contacts'] ?? [],
      );
    }
  }

  void _addEmergencyContact() async {
    final contact = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (ctx) => EmergencyContactDialog(),
    );
    if (contact != null) {
      setState(() {
        _emergencyContacts.add(contact);
      });
    }
  }

  void _editEmergencyContact(int idx) async {
    final contact = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (ctx) =>
          EmergencyContactDialog(initialData: _emergencyContacts[idx]),
    );
    if (contact != null) {
      setState(() {
        _emergencyContacts[idx] = contact;
      });
    }
  }

  void _removeEmergencyContact(int idx) {
    setState(() {
      _emergencyContacts.removeAt(idx);
    });
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Parent/Guardian',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            TextFormField(
              controller: _parentNameController,
              decoration: InputDecoration(labelText: 'Name'),
              validator: (v) => v == null || v.isEmpty ? 'Required' : null,
            ),
            TextFormField(
              controller: _parentSurnameController,
              decoration: InputDecoration(labelText: 'Surname'),
              validator: (v) => v == null || v.isEmpty ? 'Required' : null,
            ),
            TextFormField(
              controller: _parentAddressController,
              decoration: InputDecoration(labelText: 'Address'),
            ),
            TextFormField(
              controller: _parentPostalController,
              decoration: InputDecoration(labelText: 'Postal Code'),
            ),
            Row(
              children: [
                DropdownButton<String>(
                  value: _parentCountryCode,
                  items: ['+1', '+44', '+34', '+49', '+33', '+39', '+52', '+91']
                      .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                      .toList(),
                  onChanged: (v) =>
                      setState(() => _parentCountryCode = v ?? '+1'),
                ),
                Expanded(
                  child: TextFormField(
                    controller: _parentMobileController,
                    decoration: InputDecoration(labelText: 'Mobile (required)'),
                    keyboardType: TextInputType.phone,
                    validator: (v) =>
                        v == null || v.isEmpty ? 'Required' : null,
                  ),
                ),
              ],
            ),
            TextFormField(
              controller: _parentHomePhoneController,
              decoration: InputDecoration(labelText: 'Home Phone'),
              keyboardType: TextInputType.phone,
            ),
            TextFormField(
              controller: _parentWorkPhoneController,
              decoration: InputDecoration(labelText: 'Work Phone'),
              keyboardType: TextInputType.phone,
            ),
            TextFormField(
              controller: _parentEmailController,
              decoration: InputDecoration(labelText: 'Email'),
              keyboardType: TextInputType.emailAddress,
            ),
            TextFormField(
              controller: _parentWorkplaceController,
              decoration: InputDecoration(labelText: 'Workplace'),
            ),
            const SizedBox(height: 24),
            Text('Child', style: Theme.of(context).textTheme.titleLarge),
            TextFormField(
              controller: _childNameController,
              decoration: InputDecoration(labelText: 'Name'),
              validator: (v) => v == null || v.isEmpty ? 'Required' : null,
            ),
            TextFormField(
              controller: _childDobController,
              decoration: InputDecoration(
                labelText: 'Date of Birth (YYYY-MM-DD)',
              ),
              keyboardType: TextInputType.datetime,
              validator: (v) => v == null || v.isEmpty ? 'Required' : null,
            ),
            TextFormField(
              controller: _childGradeController,
              decoration: InputDecoration(labelText: 'Grade/Course'),
            ),
            TextFormField(
              controller: _childShiftController,
              decoration: InputDecoration(labelText: 'School Shift'),
            ),
            TextFormField(
              controller: _childSchoolNameController,
              decoration: InputDecoration(labelText: 'School Name'),
            ),
            TextFormField(
              controller: _childSchoolAddressController,
              decoration: InputDecoration(labelText: 'School Address'),
            ),
            TextFormField(
              controller: _childSchoolPostalController,
              decoration: InputDecoration(labelText: 'School Postal Code'),
            ),
            const SizedBox(height: 16),
            SwitchListTile(
              title: Text('Double Language/School Shift'),
              value: _doubleLanguage,
              onChanged: (val) {
                setState(() {
                  _doubleLanguage = val;
                  if (_doubleLanguage) {
                    // Default to English/German, Morning/Afternoon
                    _selectedLanguages = ['English', 'German'];
                    _selectedShifts = ['Morning', 'Afternoon'];
                  } else {
                    _selectedLanguages = ['English'];
                    _selectedShifts = ['Morning'];
                  }
                });
              },
            ),
            if (_doubleLanguage) ...[
              Row(
                children: [
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _selectedLanguages[0],
                      items: _languageOptions
                          .map(
                            (lang) => DropdownMenuItem(
                              value: lang,
                              child: Text(lang),
                            ),
                          )
                          .toList(),
                      onChanged: (val) {
                        setState(() {
                          _selectedLanguages[0] = val ?? 'English';
                        });
                      },
                      decoration: InputDecoration(labelText: 'Language 1'),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _selectedLanguages.length > 1
                          ? _selectedLanguages[1]
                          : 'German',
                      items: _languageOptions
                          .map(
                            (lang) => DropdownMenuItem(
                              value: lang,
                              child: Text(lang),
                            ),
                          )
                          .toList(),
                      onChanged: (val) {
                        setState(() {
                          if (_selectedLanguages.length > 1) {
                            _selectedLanguages[1] = val ?? 'German';
                          } else {
                            _selectedLanguages.add(val ?? 'German');
                          }
                        });
                      },
                      decoration: InputDecoration(labelText: 'Language 2'),
                    ),
                  ),
                ],
              ),
              Row(
                children: [
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _selectedShifts[0],
                      items: _shiftOptions
                          .map(
                            (shift) => DropdownMenuItem(
                              value: shift,
                              child: Text(shift),
                            ),
                          )
                          .toList(),
                      onChanged: (val) {
                        setState(() {
                          _selectedShifts[0] = val ?? 'Morning';
                        });
                      },
                      decoration: InputDecoration(labelText: 'Shift 1'),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _selectedShifts.length > 1
                          ? _selectedShifts[1]
                          : 'Afternoon',
                      items: _shiftOptions
                          .map(
                            (shift) => DropdownMenuItem(
                              value: shift,
                              child: Text(shift),
                            ),
                          )
                          .toList(),
                      onChanged: (val) {
                        setState(() {
                          if (_selectedShifts.length > 1) {
                            _selectedShifts[1] = val ?? 'Afternoon';
                          } else {
                            _selectedShifts.add(val ?? 'Afternoon');
                          }
                        });
                      },
                      decoration: InputDecoration(labelText: 'Shift 2'),
                    ),
                  ),
                ],
              ),
            ],
            const SizedBox(height: 24),
            Text(
              'Trusted Contacts',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            ..._emergencyContacts.asMap().entries.map((entry) {
              final idx = entry.key;
              final contact = entry.value;
              return Card(
                margin: const EdgeInsets.symmetric(vertical: 4),
                child: ListTile(
                  title: Text(
                    '${contact['name']} (${contact['relationship']})',
                  ),
                  subtitle: Text('Mobile: ${contact['mobile']}'),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      IconButton(
                        icon: Icon(Icons.edit),
                        onPressed: () => _editEmergencyContact(idx),
                      ),
                      IconButton(
                        icon: Icon(Icons.delete),
                        onPressed: () => _removeEmergencyContact(idx),
                      ),
                    ],
                  ),
                ),
              );
            }),
            TextButton.icon(
              icon: Icon(Icons.add),
              label: Text('Add Trusted Contact'),
              onPressed: _addEmergencyContact,
            ),
            const SizedBox(height: 24),
            Center(
              child: ElevatedButton(
                child: Text(widget.isEditing ? 'Save Changes' : 'Add'),
                onPressed: () {
                  if (_formKey.currentState?.validate() ?? false) {
                    widget.onSave({
                      'parent_name': _parentNameController.text,
                      'parent_surname': _parentSurnameController.text,
                      'parent_address': _parentAddressController.text,
                      'parent_postal': _parentPostalController.text,
                      'parent_home_phone': _parentHomePhoneController.text,
                      'parent_work_phone': _parentWorkPhoneController.text,
                      'parent_mobile': _parentMobileController.text,
                      'parent_country_code': _parentCountryCode,
                      'parent_email': _parentEmailController.text,
                      'parent_workplace': _parentWorkplaceController.text,
                      'child_name': _childNameController.text,
                      'child_dob': _childDobController.text,
                      'child_grade': _childGradeController.text,
                      'child_shift': _childShiftController.text,
                      'child_school_name': _childSchoolNameController.text,
                      'child_school_address':
                          _childSchoolAddressController.text,
                      'child_school_postal': _childSchoolPostalController.text,
                      'double_language': _doubleLanguage,
                      'double_languages': _doubleLanguage
                          ? _selectedLanguages
                          : [_selectedLanguages[0]],
                      'double_shifts': _doubleLanguage
                          ? _selectedShifts
                          : [_selectedShifts[0]],
                      'emergency_contacts': _emergencyContacts,
                    });
                  }
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class EmergencyContactDialog extends StatefulWidget {
  final Map<String, dynamic>? initialData;
  const EmergencyContactDialog({super.key, this.initialData});

  @override
  State<EmergencyContactDialog> createState() => _EmergencyContactDialogState();
}

class _EmergencyContactDialogState extends State<EmergencyContactDialog> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _surnameController = TextEditingController();
  final _mobileController = TextEditingController();
  final _homePhoneController = TextEditingController();
  final _workPhoneController = TextEditingController();
  final _addressController = TextEditingController();
  final _emailController = TextEditingController();
  String _relationship = 'Uncle';
  String _countryCode = '+1';

  @override
  void initState() {
    super.initState();
    if (widget.initialData != null) {
      final d = widget.initialData!;
      _nameController.text = d['name'] ?? '';
      _surnameController.text = d['surname'] ?? '';
      _mobileController.text = d['mobile'] ?? '';
      _homePhoneController.text = d['home_phone'] ?? '';
      _workPhoneController.text = d['work_phone'] ?? '';
      _addressController.text = d['address'] ?? '';
      _emailController.text = d['email'] ?? '';
      _relationship = d['relationship'] ?? 'Uncle';
      _countryCode = d['country_code'] ?? '+1';
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _surnameController.dispose();
    _mobileController.dispose();
    _homePhoneController.dispose();
    _workPhoneController.dispose();
    _addressController.dispose();
    _emailController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('Emergency Contact'),
      content: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<String>(
                initialValue: _relationship,
                items: ['Uncle', 'Aunt', 'Grandparent', 'Other']
                    .map((r) => DropdownMenuItem(value: r, child: Text(r)))
                    .toList(),
                onChanged: (v) => setState(() => _relationship = v ?? 'Uncle'),
                decoration: InputDecoration(labelText: 'Relationship'),
              ),
              TextFormField(
                controller: _nameController,
                decoration: InputDecoration(labelText: 'Name'),
                validator: (v) => v == null || v.isEmpty ? 'Required' : null,
              ),
              TextFormField(
                controller: _surnameController,
                decoration: InputDecoration(labelText: 'Surname'),
              ),
              Row(
                children: [
                  DropdownButton<String>(
                    value: _countryCode,
                    items:
                        ['+1', '+44', '+34', '+49', '+33', '+39', '+52', '+91']
                            .map(
                              (c) => DropdownMenuItem(value: c, child: Text(c)),
                            )
                            .toList(),
                    onChanged: (v) => setState(() => _countryCode = v ?? '+1'),
                  ),
                  Expanded(
                    child: TextFormField(
                      controller: _mobileController,
                      decoration: InputDecoration(
                        labelText: 'Mobile (required)',
                      ),
                      keyboardType: TextInputType.phone,
                      validator: (v) =>
                          v == null || v.isEmpty ? 'Required' : null,
                    ),
                  ),
                ],
              ),
              TextFormField(
                controller: _homePhoneController,
                decoration: InputDecoration(labelText: 'Home Phone'),
                keyboardType: TextInputType.phone,
              ),
              TextFormField(
                controller: _workPhoneController,
                decoration: InputDecoration(labelText: 'Work Phone'),
                keyboardType: TextInputType.phone,
              ),
              TextFormField(
                controller: _addressController,
                decoration: InputDecoration(labelText: 'Address'),
              ),
              TextFormField(
                controller: _emailController,
                decoration: InputDecoration(labelText: 'Email'),
                keyboardType: TextInputType.emailAddress,
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: () {
            if (_formKey.currentState?.validate() ?? false) {
              Navigator.of(context).pop({
                'relationship': _relationship,
                'name': _nameController.text,
                'surname': _surnameController.text,
                'mobile': _mobileController.text,
                'country_code': _countryCode,
                'home_phone': _homePhoneController.text,
                'work_phone': _workPhoneController.text,
                'address': _addressController.text,
                'email': _emailController.text,
              });
            }
          },
          child: Text('Save'),
        ),
      ],
    );
  }
}
