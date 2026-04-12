import 'package:flutter/material.dart';
import 'screens/login_screen.dart';
import 'screens/kid_home_screen.dart';

void main() => runApp(const ColePagoParentApp());

class ColePagoParentApp extends StatelessWidget {
  const ColePagoParentApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ColePago Parents',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blueAccent),
        useMaterial3: true,
      ),
      home: MainDrawerScaffold(),
    );
  }
}
