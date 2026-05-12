import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';
import 'screens/login_screen.dart';
import 'screens/parent_dashboard_screen.dart';
import 'screens/merchant_dashboard_screen.dart';
import 'screens/first_time_screen.dart';

void main() {
  runApp(const ColePagoParentsApp());
}

class ColePagoParentsApp extends StatelessWidget {
  const ColePagoParentsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ColePago Parents',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blueAccent),
        useMaterial3: true,
      ),
      home: LoginScreen(
        onLoginSuccess: (token, userId, role) async {
          final prefs = await SharedPreferences.getInstance();
          if (role == 'merchant') {
            if (!context.mounted) return;
            Navigator.of(context).pushReplacement(
              MaterialPageRoute(
                builder: (_) =>
                    MerchantDashboardScreen(token: token, merchantId: userId),
              ),
            );
            return;
          }

          final profileKey = 'profile_complete_$userId';
          bool profileComplete = prefs.getBool(profileKey) ?? false;

          if (!profileComplete) {
            // Check with the server
            try {
              final api = ApiService();
              api.setToken(token);
              final profile = await api.get('/parent/$userId/profile');
              profileComplete =
                  profile.isNotEmpty &&
                  (profile['mobile_phone'] ?? '').toString().isNotEmpty;
              if (profileComplete) {
                await prefs.setBool(profileKey, true);
              }
            } catch (_) {
              profileComplete = false;
            }
          }

          if (!context.mounted) return;
          if (profileComplete) {
            Navigator.of(context).pushReplacement(
              MaterialPageRoute(
                builder: (_) =>
                    ParentDashboardScreen(token: token, parentId: userId),
              ),
            );
          } else {
            Navigator.of(context).pushReplacement(
              MaterialPageRoute(
                builder: (_) => FirstTimeScreen(
                  token: token,
                  parentId: userId,
                  onSetupComplete: () async {
                    await prefs.setBool(profileKey, true);
                  },
                ),
              ),
            );
          }
        },
      ),
    );
  }
}
