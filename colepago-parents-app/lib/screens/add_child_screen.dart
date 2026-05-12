import 'package:flutter/material.dart';
import '../api_service.dart';

class AddChildScreen extends StatefulWidget {
  final String token;
  final int parentId;
  final int? setupTotalChildren;
  final int setupChildIndex;

  const AddChildScreen({
    super.key,
    required this.token,
    required this.parentId,
    this.setupTotalChildren,
    this.setupChildIndex = 1,
  });

  @override
  State<AddChildScreen> createState() => _AddChildScreenState();
}

class _AddChildScreenState extends State<AddChildScreen> {
  late ApiService _apiService;
  bool _saving = false;
  bool _livesWithParent = true;
  late int _currentSetupChildIndex;
  final Map<int, Map<String, dynamic>> _childDrafts = {};
  final Set<int> _savedChildIndexes = {};
  final _formKey = GlobalKey<FormState>();
  final TextEditingController _fullNameController = TextEditingController();
  final TextEditingController _mobilePhoneController = TextEditingController();
  final TextEditingController _schoolNameController = TextEditingController();
  final TextEditingController _shiftStartController = TextEditingController();
  final TextEditingController _shiftEndController = TextEditingController();
  final TextEditingController _homeAddressController = TextEditingController();
  final TextEditingController _homePhoneController = TextEditingController();
  String? _selectedSchoolId;
  String? _selectedProvince;
  String? _selectedCity;
  String? _selectedNeighborhood;
  String? _schoolAddress;
  String? _schoolPhone;
  String? _schoolEmail;
  String? _childShift;
  List<Map<String, String>> _schools = [];
  List<String> _provinces = [];
  List<String> _cities = [];
  List<String> _neighborhoods = [];
  final List<Map<String, String>> _altActivities = [];
  String? _activityPeriod = 'after_shift';
  String? _activityType;

  static const _shiftOptions = [
    'Morning',
    'Afternoon',
    'Evening',
    'Full day',
    'Other',
  ];

  static const _activityPeriods = {
    'before_shift': 'Before school shift',
    'after_shift': 'After school shift',
  };

  static const _activityTypes = [
    'Dance',
    'Language lessons',
    'Music',
    'Soccer',
    'Baseball',
    'Other sports practice',
    'Other',
  ];

  // Alt activity fields
  final TextEditingController _activityNameController = TextEditingController();
  final TextEditingController _activityStartController =
      TextEditingController();
  final TextEditingController _activityEndController = TextEditingController();
  final TextEditingController _activityAddressController =
      TextEditingController();
  final TextEditingController _activityInstitutionController =
      TextEditingController();
  final TextEditingController _activityPhoneController =
      TextEditingController();
  final TextEditingController _activityProfessorController =
      TextEditingController();

  @override
  void initState() {
    super.initState();
    final total = widget.setupTotalChildren;
    _currentSetupChildIndex = total == null
        ? widget.setupChildIndex
        : widget.setupChildIndex.clamp(1, total);
    _apiService = ApiService();
    _apiService.setToken(widget.token);
    _fetchProvinces();
  }

  @override
  void dispose() {
    _fullNameController.dispose();
    _mobilePhoneController.dispose();
    _schoolNameController.dispose();
    _shiftStartController.dispose();
    _shiftEndController.dispose();
    _homeAddressController.dispose();
    _homePhoneController.dispose();
    _activityNameController.dispose();
    _activityStartController.dispose();
    _activityEndController.dispose();
    _activityAddressController.dispose();
    _activityInstitutionController.dispose();
    _activityPhoneController.dispose();
    _activityProfessorController.dispose();
    super.dispose();
  }

  Future<void> _fetchProvinces() async {
    try {
      final data = await _apiService.get('/geo/provinces');
      setState(() {
        _provinces = List<String>.from(data['provinces'] ?? []);
      });
    } catch (e) {
      setState(() {
        _provinces = [];
      });
    }
  }

  Future<void> _fetchCities(String province) async {
    try {
      final data = await _apiService.get(
        Uri(
          path: '/geo/cities',
          queryParameters: {'province': province},
        ).toString(),
      );
      setState(() {
        _cities = List<String>.from(data['cities'] ?? []);
      });
    } catch (e) {
      setState(() {
        _cities = [];
      });
    }
  }

  Future<void> _fetchNeighborhoods(String province, String city) async {
    try {
      final data = await _apiService.get(
        Uri(
          path: '/geo/neighborhoods',
          queryParameters: {'province': province, 'city': city},
        ).toString(),
      );
      final neighborhoods = List<String>.from(data['neighborhoods'] ?? []);
      setState(() {
        _neighborhoods = neighborhoods;
      });
      if (neighborhoods.isEmpty) {
        await _fetchSchools(province: province, city: city);
      }
    } catch (e) {
      setState(() {
        _neighborhoods = [];
      });
      await _fetchSchools(province: province, city: city);
    }
  }

  Future<void> _fetchSchools({
    required String province,
    required String city,
    String? neighborhood,
  }) async {
    try {
      final params = {'province': province, 'city': city};
      if (neighborhood != null && neighborhood.isNotEmpty) {
        params['neighborhood'] = neighborhood;
      }
      final data = await _apiService.get(
        Uri(path: '/geo/schools', queryParameters: params).toString(),
      );
      setState(() {
        _schools = List<Map<String, String>>.from(
          (data['schools'] ?? []).map(
            (s) => Map<String, String>.from(
              (s as Map).map(
                (key, value) =>
                    MapEntry(key.toString(), value?.toString() ?? ''),
              ),
            ),
          ),
        );
      });
    } catch (e) {
      setState(() {
        _schools = [];
      });
    }
  }

  void _onSchoolSelected(String? schoolId) {
    final school = _schools.firstWhere(
      (s) => s['id'] == schoolId,
      orElse: () => {},
    );
    setState(() {
      _selectedSchoolId = schoolId;
      _schoolNameController.text = school['name'] ?? _schoolNameController.text;
      _schoolAddress = school['address'];
      _schoolPhone = school['phone'];
      _schoolEmail = school['email'];
    });
  }

  void _addAltActivity() {
    if (_activityType == null && _activityNameController.text.isEmpty) return;
    setState(() {
      _altActivities.add({
        'period': _activityPeriod ?? 'after_shift',
        'type': _activityType ?? 'Other',
        'name': _activityNameController.text,
        'start': _activityStartController.text,
        'end': _activityEndController.text,
        'address': _activityAddressController.text,
        'institution': _activityInstitutionController.text,
        'phone': _activityPhoneController.text,
        'professor': _activityProfessorController.text,
      });
      _activityPeriod = 'after_shift';
      _activityType = null;
      _activityNameController.clear();
      _activityStartController.clear();
      _activityEndController.clear();
      _activityAddressController.clear();
      _activityInstitutionController.clear();
      _activityPhoneController.clear();
      _activityProfessorController.clear();
    });
  }

  void _captureCurrentDraft() {
    _childDrafts[_currentSetupChildIndex] = {
      'full_name': _fullNameController.text,
      'mobile_phone': _mobilePhoneController.text,
      'school_name': _schoolNameController.text,
      'shift_start': _shiftStartController.text,
      'shift_end': _shiftEndController.text,
      'home_address': _homeAddressController.text,
      'home_phone': _homePhoneController.text,
      'lives_with_parent': _livesWithParent,
      'school_id': _selectedSchoolId,
      'province': _selectedProvince,
      'city': _selectedCity,
      'neighborhood': _selectedNeighborhood,
      'school_address': _schoolAddress,
      'school_phone': _schoolPhone,
      'school_email': _schoolEmail,
      'shift': _childShift,
      'activity_period': _activityPeriod,
      'activity_type': _activityType,
      'activities': _altActivities
          .map((item) => Map<String, String>.from(item))
          .toList(),
    };
  }

  Future<void> _loadDraftForChild(int index) async {
    final draft = _childDrafts[index];
    _formKey.currentState?.reset();
    _fullNameController.text = draft?['full_name']?.toString() ?? '';
    _mobilePhoneController.text = draft?['mobile_phone']?.toString() ?? '';
    _schoolNameController.text = draft?['school_name']?.toString() ?? '';
    _shiftStartController.text = draft?['shift_start']?.toString() ?? '';
    _shiftEndController.text = draft?['shift_end']?.toString() ?? '';
    _homeAddressController.text = draft?['home_address']?.toString() ?? '';
    _homePhoneController.text = draft?['home_phone']?.toString() ?? '';

    final province = draft?['province']?.toString();
    final city = draft?['city']?.toString();
    final neighborhood = draft?['neighborhood']?.toString();
    setState(() {
      _currentSetupChildIndex = index;
      _livesWithParent = draft?['lives_with_parent'] as bool? ?? true;
      _selectedSchoolId = draft?['school_id']?.toString();
      _selectedProvince = province;
      _selectedCity = city;
      _selectedNeighborhood = neighborhood;
      _schoolAddress = draft?['school_address']?.toString();
      _schoolPhone = draft?['school_phone']?.toString();
      _schoolEmail = draft?['school_email']?.toString();
      _childShift = draft?['shift']?.toString();
      _activityPeriod = draft?['activity_period']?.toString() ?? 'after_shift';
      _activityType = draft?['activity_type']?.toString();
      _altActivities
        ..clear()
        ..addAll(
          ((draft?['activities'] as List?) ?? []).map(
            (item) => Map<String, String>.from(item as Map),
          ),
        );
      _cities = [];
      _neighborhoods = [];
      _schools = [];
    });

    if (province != null && province.isNotEmpty) {
      await _fetchCities(province);
    }
    if (province != null &&
        city != null &&
        province.isNotEmpty &&
        city.isNotEmpty) {
      await _fetchNeighborhoods(province, city);
    }
    if (province != null &&
        city != null &&
        province.isNotEmpty &&
        city.isNotEmpty) {
      await _fetchSchools(
        province: province,
        city: city,
        neighborhood: neighborhood?.isNotEmpty == true ? neighborhood : null,
      );
    }
  }

  Future<void> _goToSetupChild(int index) async {
    final total = widget.setupTotalChildren;
    if (total == null) return;
    final nextIndex = index.clamp(1, total);
    if (nextIndex == _currentSetupChildIndex) return;
    _captureCurrentDraft();
    await _loadDraftForChild(nextIndex);
  }

  Future<void> _saveChild() async {
    final total = widget.setupTotalChildren;
    if (total != null && _currentSetupChildIndex > total) {
      Navigator.pop(context, true);
      return;
    }
    if (total != null && _savedChildIndexes.contains(_currentSetupChildIndex)) {
      final nextOpenIndex = List<int>.generate(total, (i) => i + 1).firstWhere(
        (index) => !_savedChildIndexes.contains(index),
        orElse: () => total + 1,
      );
      if (nextOpenIndex > total) {
        Navigator.pop(context, true);
      } else {
        await _goToSetupChild(nextOpenIndex);
      }
      return;
    }
    if (!_formKey.currentState!.validate()) return;
    _captureCurrentDraft();
    setState(() => _saving = true);
    try {
      final payload = {
        'parent_id': widget.parentId,
        'full_name': _fullNameController.text,
        'mobile_phone': _mobilePhoneController.text,
        'school_id': _selectedSchoolId,
        'school_name': _schoolNameController.text,
        'shift': _childShift,
        'shift_start': _shiftStartController.text,
        'shift_end': _shiftEndController.text,
        'activities': _altActivities,
        'lives_with_parent': _livesWithParent,
        if (!_livesWithParent) 'home_address': _homeAddressController.text,
        if (!_livesWithParent) 'home_phone': _homePhoneController.text,
      };
      await _apiService.post('/parent/add-child', payload);
      if (!mounted) return;
      if (total != null) {
        _savedChildIndexes.add(_currentSetupChildIndex);
      }

      final hasNextSetupChild =
          total != null && _currentSetupChildIndex < total;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            hasNextSetupChild
                ? 'Child $_currentSetupChildIndex saved. Add child ${_currentSetupChildIndex + 1} of $total.'
                : 'Child added successfully!',
          ),
        ),
      );

      if (total != null && _savedChildIndexes.length >= total) {
        Navigator.pop(context, true);
      } else if (hasNextSetupChild) {
        await _loadDraftForChild(_currentSetupChildIndex + 1);
      } else {
        final nextOpenIndex = total == null
            ? null
            : List<int>.generate(total, (i) => i + 1).firstWhere(
                (index) => !_savedChildIndexes.contains(index),
                orElse: () => total + 1,
              );
        if (nextOpenIndex != null && total != null && nextOpenIndex <= total) {
          await _loadDraftForChild(nextOpenIndex);
        } else {
          Navigator.pop(context, true);
        }
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to add child: \\${e.toString()}')),
      );
    } finally {
      if (mounted) {
        setState(() => _saving = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final total = widget.setupTotalChildren;
    final isSetupFlow = total != null && total > 1;
    final displayIndex = total == null
        ? _currentSetupChildIndex
        : _currentSetupChildIndex.clamp(1, total);
    return Scaffold(
      appBar: AppBar(
        title: Text(
          isSetupFlow ? 'Add Child $displayIndex of $total' : 'Add Child',
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (isSetupFlow) ...[
                LinearProgressIndicator(
                  value: ((displayIndex - 1) / total).clamp(0.0, 1.0),
                ),
                const SizedBox(height: 12),
                Text(
                  'Child $displayIndex of $total',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    OutlinedButton.icon(
                      icon: const Icon(Icons.chevron_left),
                      label: const Text('Previous'),
                      onPressed: displayIndex <= 1
                          ? null
                          : () => _goToSetupChild(displayIndex - 1),
                    ),
                    OutlinedButton.icon(
                      icon: const Icon(Icons.chevron_right),
                      label: const Text('Next'),
                      onPressed: displayIndex >= total
                          ? null
                          : () => _goToSetupChild(displayIndex + 1),
                    ),
                    if (_savedChildIndexes.contains(displayIndex))
                      const Chip(label: Text('Saved')),
                  ],
                ),
                const SizedBox(height: 16),
              ],
              TextFormField(
                controller: _fullNameController,
                decoration: const InputDecoration(labelText: 'Full Name'),
                validator: (v) => v == null || v.isEmpty ? 'Required' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _mobilePhoneController,
                decoration: const InputDecoration(
                  labelText: 'Kid phone number',
                  helperText: 'Must be unique for each child.',
                ),
                keyboardType: TextInputType.phone,
                validator: (v) =>
                    v == null || v.trim().isEmpty ? 'Required' : null,
              ),
              const SizedBox(height: 12),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('Does this child live with you?'),
                subtitle: const Text('Uses your home address and phone.'),
                value: _livesWithParent,
                onChanged: (value) => setState(() => _livesWithParent = value),
              ),
              if (!_livesWithParent) ...[
                const SizedBox(height: 12),
                TextFormField(
                  controller: _homeAddressController,
                  decoration: const InputDecoration(
                    labelText: 'Child home address',
                  ),
                  validator: (v) =>
                      v == null || v.trim().isEmpty ? 'Required' : null,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _homePhoneController,
                  decoration: const InputDecoration(
                    labelText: 'Child home phone',
                  ),
                  keyboardType: TextInputType.phone,
                ),
              ],
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                initialValue: _selectedProvince,
                items: _provinces
                    .map((p) => DropdownMenuItem(value: p, child: Text(p)))
                    .toList(),
                onChanged: (province) {
                  setState(() {
                    _selectedProvince = province;
                    _selectedCity = null;
                    _selectedNeighborhood = null;
                    _selectedSchoolId = null;
                    _cities = [];
                    _neighborhoods = [];
                    _schools = [];
                    _schoolNameController.clear();
                  });
                  if (province != null) _fetchCities(province);
                },
                decoration: const InputDecoration(
                  labelText: 'State / Province',
                ),
                validator: (v) => v == null ? 'Required' : null,
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                key: ValueKey('city-$_selectedProvince'),
                initialValue: _selectedCity,
                items: _cities
                    .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                    .toList(),
                onChanged: (city) {
                  setState(() {
                    _selectedCity = city;
                    _selectedNeighborhood = null;
                    _selectedSchoolId = null;
                    _neighborhoods = [];
                    _schools = [];
                    _schoolNameController.clear();
                  });
                  if (_selectedProvince != null && city != null) {
                    _fetchNeighborhoods(_selectedProvince!, city);
                  }
                },
                decoration: const InputDecoration(labelText: 'City'),
                validator: (v) => v == null ? 'Required' : null,
              ),
              const SizedBox(height: 16),
              if (_neighborhoods.isNotEmpty) ...[
                DropdownButtonFormField<String>(
                  key: ValueKey('neighborhood-$_selectedCity'),
                  initialValue: _selectedNeighborhood,
                  items: _neighborhoods
                      .map((n) => DropdownMenuItem(value: n, child: Text(n)))
                      .toList(),
                  onChanged: (neigh) {
                    setState(() {
                      _selectedNeighborhood = neigh;
                      _selectedSchoolId = null;
                      _schools = [];
                      _schoolNameController.clear();
                    });
                    if (_selectedProvince != null &&
                        _selectedCity != null &&
                        neigh != null) {
                      _fetchSchools(
                        province: _selectedProvince!,
                        city: _selectedCity!,
                        neighborhood: neigh,
                      );
                    }
                  },
                  decoration: const InputDecoration(
                    labelText: 'Neighborhood / comuna',
                  ),
                ),
                const SizedBox(height: 16),
              ],
              DropdownButtonFormField<String>(
                key: ValueKey('school-$_selectedCity-$_selectedNeighborhood'),
                initialValue: _selectedSchoolId,
                items: _schools
                    .map(
                      (s) => DropdownMenuItem(
                        value: s['id'],
                        child: Text(s['name']!),
                      ),
                    )
                    .toList(),
                onChanged: _onSchoolSelected,
                decoration: const InputDecoration(
                  labelText: 'Search/select school',
                ),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _schoolNameController,
                decoration: const InputDecoration(
                  labelText: 'School attending',
                  helperText: 'Required. Search can fill this, or type it.',
                ),
                validator: (v) =>
                    v == null || v.trim().isEmpty ? 'Required' : null,
              ),
              if (_selectedSchoolId != null) ...[
                const SizedBox(height: 8),
                Text(
                  'School Info:',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                Text('Address: ${_schoolAddress ?? ''}'),
                Text('Phone: ${_schoolPhone ?? ''}'),
                Text('Email: ${_schoolEmail ?? ''}'),
              ],
              const SizedBox(height: 16),
              const Card(
                child: Padding(
                  padding: EdgeInsets.all(12),
                  child: Text(
                    'We ask for school, shift, route, and activity details so parents can be warned if a child separates from the normal walk, bus, school route, or expected activity schedule.',
                  ),
                ),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _childShift,
                items: _shiftOptions
                    .map(
                      (shift) =>
                          DropdownMenuItem(value: shift, child: Text(shift)),
                    )
                    .toList(),
                onChanged: (shift) => setState(() => _childShift = shift),
                decoration: const InputDecoration(labelText: 'School shift'),
                validator: (v) => v == null ? 'Required' : null,
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: _shiftStartController,
                      decoration: const InputDecoration(
                        labelText: 'Shift starts',
                        hintText: '08:00',
                      ),
                      validator: (v) =>
                          v == null || v.trim().isEmpty ? 'Required' : null,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: TextFormField(
                      controller: _shiftEndController,
                      decoration: const InputDecoration(
                        labelText: 'Shift ends',
                        hintText: '15:00',
                      ),
                      validator: (v) =>
                          v == null || v.trim().isEmpty ? 'Required' : null,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),
              Text(
                'Alternative Activities',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              ..._altActivities.map(
                (a) => ListTile(
                  title: Text(a['name'] ?? ''),
                  subtitle: Text(
                    '${_activityPeriods[a['period']] ?? a['period']} - ${a['type']} - Time: ${a['start']} - ${a['end']}, Place: ${a['institution']}, Address: ${a['address']}, Phone: ${a['phone']}, Professor: ${a['professor']}',
                  ),
                ),
              ),
              const SizedBox(height: 8),
              DropdownButtonFormField<String>(
                initialValue: _activityPeriod,
                items: _activityPeriods.entries
                    .map(
                      (entry) => DropdownMenuItem(
                        value: entry.key,
                        child: Text(entry.value),
                      ),
                    )
                    .toList(),
                onChanged: (value) => setState(() => _activityPeriod = value),
                decoration: const InputDecoration(labelText: 'When'),
              ),
              const SizedBox(height: 8),
              DropdownButtonFormField<String>(
                initialValue: _activityType,
                items: _activityTypes
                    .map(
                      (type) =>
                          DropdownMenuItem(value: type, child: Text(type)),
                    )
                    .toList(),
                onChanged: (value) => setState(() => _activityType = value),
                decoration: const InputDecoration(labelText: 'Activity type'),
              ),
              const SizedBox(height: 8),
              TextFormField(
                controller: _activityNameController,
                decoration: const InputDecoration(
                  labelText: 'Activity name / detail',
                  hintText: 'e.g. Soccer practice, Piano, English lessons',
                ),
              ),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: _activityStartController,
                      decoration: const InputDecoration(
                        labelText: 'Start Time',
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: TextFormField(
                      controller: _activityEndController,
                      decoration: const InputDecoration(labelText: 'End Time'),
                    ),
                  ),
                ],
              ),
              TextFormField(
                controller: _activityAddressController,
                decoration: const InputDecoration(
                  labelText: 'Activity place address',
                ),
              ),
              TextFormField(
                controller: _activityInstitutionController,
                decoration: const InputDecoration(
                  labelText: 'Activity place name',
                ),
              ),
              TextFormField(
                controller: _activityPhoneController,
                decoration: const InputDecoration(
                  labelText: 'Activity place phone',
                ),
                keyboardType: TextInputType.phone,
              ),
              TextFormField(
                controller: _activityProfessorController,
                decoration: const InputDecoration(labelText: 'Professor Name'),
              ),
              Align(
                alignment: Alignment.centerRight,
                child: ElevatedButton.icon(
                  icon: const Icon(Icons.add),
                  label: const Text('Add Activity'),
                  onPressed: _addAltActivity,
                ),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _saving ? null : _saveChild,
                  child: _saving
                      ? const SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : Text(
                          isSetupFlow && _currentSetupChildIndex < total
                              ? 'Save and Add Next Child'
                              : 'Save Child',
                        ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
