import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../api_service.dart';

class KidLoginScreen extends StatefulWidget {
  final void Function(String token, int kidId) onLoginSuccess;

  const KidLoginScreen({super.key, required this.onLoginSuccess});

  @override
  State<KidLoginScreen> createState() => _KidLoginScreenState();
}

class _KidLoginScreenState extends State<KidLoginScreen> {
  final _api = ApiService();
  final _formKey = GlobalKey<FormState>();
  final _parentEmailCtrl = TextEditingController();
  final _parentPasswordCtrl = TextEditingController();
  final _childPhoneCtrl = TextEditingController();
  bool _loading = false;
  String? _error;

  String? _validateEmail(String? value) {
    final email = (value ?? '').trim();
    if (email.isEmpty) return 'Parent email is required';
    final valid = RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$').hasMatch(email);
    return valid ? null : 'Enter a valid email address';
  }

  @override
  void initState() {
    super.initState();
    _tryAutoLogin();
  }

  @override
  void dispose() {
    _parentEmailCtrl.dispose();
    _parentPasswordCtrl.dispose();
    _childPhoneCtrl.dispose();
    super.dispose();
  }

  Future<void> _tryAutoLogin() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('kid_auth_token');
    final kidId = prefs.getInt('kid_id');
    if (token != null && kidId != null) {
      widget.onLoginSuccess(token, kidId);
    }
  }

  Future<void> _activateKidApp() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final response = await _api.kidLogin(
        parentEmail: _parentEmailCtrl.text.trim(),
        parentPassword: _parentPasswordCtrl.text,
        childMobilePhone: _childPhoneCtrl.text.trim(),
      );
      final token = response['token'] ?? response['access_token'];
      final kidId = response['kid_id'] ?? response['child_id'];
      if (token == null || kidId == null) {
        throw Exception('Kid access could not be activated');
      }
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('kid_auth_token', token.toString());
      await prefs.setInt(
        'kid_id',
        kidId is int ? kidId : int.parse(kidId.toString()),
      );
      if (!mounted) return;
      widget.onLoginSuccess(
        token.toString(),
        kidId is int ? kidId : int.parse(kidId.toString()),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString().replaceFirst('Exception: ', '');
      });
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('ColePago Kids')),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Form(
                key: _formKey,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Image.asset(
                      'assets/branding/colepago_logo.png',
                      height: 150,
                      fit: BoxFit.contain,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'Activate kid access',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.headlineSmall,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Use the same ColePago identity with the child phone number.',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                    const SizedBox(height: 24),
                    TextFormField(
                      controller: _parentEmailCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Parent email',
                        border: OutlineInputBorder(),
                      ),
                      keyboardType: TextInputType.emailAddress,
                      validator: _validateEmail,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _parentPasswordCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Parent password',
                        border: OutlineInputBorder(),
                      ),
                      obscureText: true,
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Parent password is required';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _childPhoneCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Kid phone number',
                        border: OutlineInputBorder(),
                      ),
                      keyboardType: TextInputType.phone,
                      validator: (value) {
                        if (value == null || value.trim().isEmpty) {
                          return 'Kid phone number is required';
                        }
                        return null;
                      },
                    ),
                    if (_error != null) ...[
                      const SizedBox(height: 12),
                      Text(_error!, style: const TextStyle(color: Colors.red)),
                    ],
                    const SizedBox(height: 20),
                    FilledButton.icon(
                      icon: _loading
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.lock_open),
                      label: const Text('Activate'),
                      onPressed: _loading ? null : _activateKidApp,
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
