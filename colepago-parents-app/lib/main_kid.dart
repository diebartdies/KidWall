import 'package:flutter/material.dart';

void main() => runApp(const MinimalKidApp());

class MinimalKidApp extends StatelessWidget {
  const MinimalKidApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        appBar: AppBar(title: const Text('Kids App Test')),
        body: const Center(child: Text('Kids App Launched!')),
      ),
    );
  }
}
