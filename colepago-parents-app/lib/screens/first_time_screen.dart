import 'package:flutter/material.dart';
import 'parent_profile_form_screen.dart';
import 'add_child_screen.dart';

class FirstTimeScreen extends StatelessWidget {
  final String token;
  final int parentId;
  final VoidCallback onSetupComplete;

  const FirstTimeScreen({
    super.key,
    required this.token,
    required this.parentId,
    required this.onSetupComplete,
  });

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
                              token: token,
                              parentId: parentId,
                            ),
                          ),
                        );
                        if (completed == true) onSetupComplete();
                      },
                    ),
                    const SizedBox(width: 24),
                    _SetupCard(
                      icon: Icons.child_care,
                      label: 'Add Kid',
                      color: const Color(0xFF00897B),
                      onTap: () async {
                        final completed = await Navigator.push<bool>(
                          context,
                          MaterialPageRoute(
                            builder: (_) => AddChildScreen(
                              token: token,
                              parentId: parentId,
                            ),
                          ),
                        );
                        if (completed == true) onSetupComplete();
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
