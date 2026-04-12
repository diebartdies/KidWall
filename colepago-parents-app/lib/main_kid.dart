import 'package:flutter/material.dart';
import 'screens/kid_home_screen.dart';

void main() => runApp(const ColePagoKidApp());

class ColePagoKidApp extends StatelessWidget {
  const ColePagoKidApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ColePago Kid',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.orange),
        useMaterial3: true,
      ),
      home: const KidHomeScreen(),
    );
  }
}
