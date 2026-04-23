import 'package:flutter/material.dart';
import 'screens/kid_home_screen.dart';
import 'screens/login_screen.dart';

void main() {
  runApp(const ColePagoKidsApp());
}

class ColePagoKidsApp extends StatelessWidget {
  const ColePagoKidsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ColePago Kids',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blueAccent),
        useMaterial3: true,
      ),
      home: const KidsAuthFlow(),
    );
  }
}

class KidsAuthFlow extends StatefulWidget {
  const KidsAuthFlow({super.key});

  @override
  State<KidsAuthFlow> createState() => _KidsAuthFlowState();
}

class _KidsAuthFlowState extends State<KidsAuthFlow> {
  String? _token;
  int? _kidId;

  void _onLoginSuccess(String token, int kidId) {
    setState(() {
      _token = token;
      _kidId = kidId;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_token == null || _kidId == null) {
      return LoginScreen(onLoginSuccess: _onLoginSuccess);
    } else {
      return KidHomeScreen(); // Pass token/kidId if needed
    }
  }
}
