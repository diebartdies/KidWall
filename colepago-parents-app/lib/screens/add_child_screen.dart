import 'package:flutter/material.dart';
import '../api_service.dart';

class AddChildScreen extends StatefulWidget {
  final String token;
  final int parentId;
  const AddChildScreen({
    super.key,
    required this.token,
    required this.parentId,
  });

  @override
  State<AddChildScreen> createState() => _AddChildScreenState();
}

class _AddChildScreenState extends State<AddChildScreen> {
  late ApiService _apiService;
  bool _saving = false;
  final _formKey = GlobalKey<FormState>();
  final TextEditingController _fullNameController = TextEditingController();
  String? _selectedSchoolId;
  String? _selectedCity;
  String? _selectedNeighborhood;
  String? _schoolAddress;
  String? _schoolPhone;
  String? _schoolEmail;
  String? _childShift;
  List<Map<String, String>> _schools = [];
  List<String> _cities = [];
  List<String> _neighborhoods = [];
  final List<Map<String, String>> _altActivities = [];

  // Alt activity fields
  final TextEditingController _activityNameController = TextEditingController();
  final TextEditingController _activityStartController =
      TextEditingController();
  final TextEditingController _activityEndController = TextEditingController();
  final TextEditingController _activityAddressController =
      TextEditingController();
  final TextEditingController _activityInstitutionController =
      TextEditingController();
  final TextEditingController _activityProfessorController =
      TextEditingController();

  @override
  void initState() {
    super.initState();
    _apiService = ApiService();
    _apiService.setToken(widget.token);
    _fetchCities();
  }

  Future<void> _fetchCities() async {
    try {
      final data = await _apiService.get('/geo/cities');
      setState(() {
        _cities = List<String>.from(data['cities'] ?? []);
      });
    } catch (e) {
      setState(() {
        _cities = [];
      });
    }
  }

  Future<void> _fetchNeighborhoods(String city) async {
    try {
      final data = await _apiService.get('/geo/neighborhoods?city=$city');
      setState(() {
        _neighborhoods = List<String>.from(data['neighborhoods'] ?? []);
      });
    } catch (e) {
      setState(() {
        _neighborhoods = [];
      });
    }
  }

  Future<void> _fetchSchools(String city, String neighborhood) async {
    try {
      final data = await _apiService.get(
        '/geo/schools?city=$city&neighborhood=$neighborhood',
      );
      setState(() {
        _schools = List<Map<String, String>>.from(
          (data['schools'] ?? []).map((s) => Map<String, String>.from(s)),
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
      _schoolAddress = school['address'];
      _schoolPhone = school['phone'];
      _schoolEmail = school['email'];
    });
  }

  void _addAltActivity() {
    if (_activityNameController.text.isEmpty) return;
    setState(() {
      _altActivities.add({
        'name': _activityNameController.text,
        'start': _activityStartController.text,
        'end': _activityEndController.text,
        'address': _activityAddressController.text,
        'institution': _activityInstitutionController.text,
        'professor': _activityProfessorController.text,
      });
      _activityNameController.clear();
      _activityStartController.clear();
      _activityEndController.clear();
      _activityAddressController.clear();
      _activityInstitutionController.clear();
      _activityProfessorController.clear();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Add Child')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextFormField(
                controller: _fullNameController,
                decoration: const InputDecoration(labelText: 'Full Name'),
                validator: (v) => v == null || v.isEmpty ? 'Required' : null,
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                initialValue: _selectedCity,
                items: _cities
                    .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                    .toList(),
                onChanged: (city) {
                  setState(() {
                    _selectedCity = city;
                    _selectedNeighborhood = null;
                    _selectedSchoolId = null;
                    _schools = [];
                  });
                  if (city != null) _fetchNeighborhoods(city);
                },
                decoration: const InputDecoration(labelText: 'City'),
                validator: (v) => v == null ? 'Required' : null,
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: _selectedNeighborhood,
                items: _neighborhoods
                    .map((n) => DropdownMenuItem(value: n, child: Text(n)))
                    .toList(),
                onChanged: (neigh) {
                  setState(() {
                    _selectedNeighborhood = neigh;
                    _selectedSchoolId = null;
                  });
                  if (_selectedCity != null && neigh != null)
                    _fetchSchools(_selectedCity!, neigh);
                },
                decoration: const InputDecoration(labelText: 'Neighborhood'),
                validator: (v) => v == null ? 'Required' : null,
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: _selectedSchoolId,
                items: _schools
                    .map(
                      (s) => DropdownMenuItem(
                        value: s['id'],
                        child: Text(s['name']!),
                      ),
                    )
                    .toList(),
                onChanged: _onSchoolSelected,
                decoration: const InputDecoration(labelText: 'School'),
                validator: (v) => v == null ? 'Required' : null,
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
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  value: _childShift,
                  items:
                      (_schools
                                  .firstWhere(
                                    (s) => s['id'] == _selectedSchoolId,
                                  )['shifts']
                                  ?.split(',') ??
                              [])
                          .map(
                            (shift) => DropdownMenuItem(
                              value: shift,
                              child: Text(shift),
                            ),
                          )
                          .toList(),
                  onChanged: (shift) => setState(() => _childShift = shift),
                  decoration: const InputDecoration(labelText: 'Child Shift'),
                  validator: (v) => v == null ? 'Required' : null,
                ),
              ],
              const SizedBox(height: 24),
              Text(
                'Alternative Activities',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              ..._altActivities.map(
                (a) => ListTile(
                  title: Text(a['name'] ?? ''),
                  subtitle: Text(
                    'Time: ${a['start']} - ${a['end']}, Address: ${a['address']}, Institution: ${a['institution']}, Professor: ${a['professor']}',
                  ),
                ),
              ),
              const SizedBox(height: 8),
              TextFormField(
                controller: _activityNameController,
                decoration: const InputDecoration(labelText: 'Activity Name'),
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
                  labelText: 'Activity Address',
                ),
              ),
              TextFormField(
                controller: _activityInstitutionController,
                decoration: const InputDecoration(labelText: 'Institution'),
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
                  onPressed: _saving
                      ? null
                      : () async {
                          if (_formKey.currentState!.validate()) {
                            setState(() => _saving = true);
                            try {
                              final payload = {
                                'parent_id': widget.parentId,
                                'full_name': _fullNameController.text,
                                'school_id': _selectedSchoolId,
                                'shift': _childShift,
                                'activities': _altActivities,
                              };
                              await _apiService.post(
                                '/parent/add-child',
                                payload,
                              );
                              if (!mounted) return;
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text('Child added successfully!'),
                                ),
                              );
                              Navigator.pop(context, true);
                            } catch (e) {
                              if (!mounted) return;
                              // ignore: use_build_context_synchronously
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text(
                                    'Failed to add child: \\${e.toString()}',
                                  ),
                                ),
                              );
                            } finally {
                              setState(() => _saving = false);
                            }
                          }
                        },
                  child: _saving
                      ? const SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Save Child'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
