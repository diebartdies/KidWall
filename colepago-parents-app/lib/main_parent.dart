import 'package:flutter/material.dart';
import 'screens/login_screen.dart';
import 'screens/parent_dashboard_screen.dart';

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
        onLoginSuccess: (token, parentId) {
          Navigator.of(context).pushReplacement(
            MaterialPageRoute(
              builder: (context) =>
                  ParentDashboardScreen(token: token, parentId: parentId),
            ),
          );
        },
      ),
    );
  }
}
