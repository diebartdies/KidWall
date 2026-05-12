import 'package:flutter/material.dart';
import '../api_service.dart';
import 'parent_profile_form_screen.dart';
import 'add_child_screen.dart';
import 'parent_dashboard_screen.dart';

class FirstTimeScreen extends StatefulWidget {
  final String token;
  final int parentId;
  final Future<void> Function() onSetupComplete;

  const FirstTimeScreen({
    super.key,
    required this.token,
    required this.parentId,
    required this.onSetupComplete,
  });

  @override
  State<FirstTimeScreen> createState() => _FirstTimeScreenState();
}

class _FirstTimeScreenState extends State<FirstTimeScreen> {
  Future<int> _childrenCount() async {
    try {
      final api = ApiService();
      api.setToken(widget.token);
      final profile = await api.get('/parent/${widget.parentId}/profile');
      final value = profile['children_using_colepago'];
      if (value is int && value > 0) return value;
      return int.tryParse(value.toString()) ?? 1;
    } catch (_) {
      return 1;
    }
  }

  Future<void> _openChildrenSetup() async {
    final count = await _childrenCount();
    if (!mounted) return;
    final completed = await Navigator.push<bool>(
      context,
      MaterialPageRoute(
        builder: (_) => AddChildScreen(
          token: widget.token,
          parentId: widget.parentId,
          setupTotalChildren: count,
        ),
      ),
    );
    if (completed == true) await _completeSetup();
  }

  Future<void> _completeSetup() async {
    await widget.onSetupComplete();
    if (!mounted) return;
    await _showKidInstallPrompt();
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(
        builder: (_) => ParentDashboardScreen(
          token: widget.token,
          parentId: widget.parentId,
        ),
      ),
    );
  }

  Future<void> _showKidInstallPrompt() {
    return showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Install Kid APK'),
        content: const Text(
          'Install ColePago Kids on the child phone. Activate it with the parent email, parent password, and the kid phone number. Configure fingerprint, face or eye detection, or a stored password fallback. Then test access and confirm the buckets are visible clearly before loading money.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text('Continue to Dashboard'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text("I'll do it now"),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA),
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text(
                  'Welcome to ColePago',
                  style: TextStyle(
                    fontSize: 26,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF1A237E),
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 12),
                const Text(
                  "Let's get you set up. Choose where to start:",
                  style: TextStyle(fontSize: 15, color: Colors.black54),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 48),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    _SetupCard(
                      icon: Icons.person_add,
                      label: 'Add Parent',
                      color: const Color(0xFF3F51B5),
                      onTap: () async {
                        final completed = await Navigator.push<bool>(
                          context,
                          MaterialPageRoute(
                            builder: (_) => ParentProfileFormScreen(
                              token: widget.token,
                              parentId: widget.parentId,
                            ),
                          ),
                        );
                        if (completed == true) {
                          await _openChildrenSetup();
                        }
                      },
                    ),
                    const SizedBox(width: 24),
                    _SetupCard(
                      icon: Icons.child_care,
                      label: 'Add Kid',
                      color: const Color(0xFF00897B),
                      onTap: () async {
                        final count = await _childrenCount();
                        if (!context.mounted) return;
                        final completed = await Navigator.push<bool>(
                          context,
                          MaterialPageRoute(
                            builder: (_) => AddChildScreen(
                              token: widget.token,
                              parentId: widget.parentId,
                              setupTotalChildren: count,
                            ),
                          ),
                        );
                        if (completed == true) await _completeSetup();
                      },
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _SetupCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  const _SetupCard({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 130,
        height: 140,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(
              color: color.withValues(alpha: 0.15),
              blurRadius: 16,
              offset: const Offset(0, 6),
            ),
          ],
          border: Border.all(color: color.withValues(alpha: 0.25), width: 1.5),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Stack(
              alignment: Alignment.topRight,
              children: [
                Icon(icon, size: 52, color: color),
                Container(
                  width: 20,
                  height: 20,
                  decoration: BoxDecoration(
                    color: color,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.add, size: 14, color: Colors.white),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              label,
              style: TextStyle(
                fontWeight: FontWeight.w600,
                fontSize: 15,
                color: color,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
