import 'package:flutter/material.dart';
import 'package:colepago_parents_app/biometric_auth.dart';

class KidHomeScreen extends StatefulWidget {
  const KidHomeScreen({super.key});

  @override
  State<KidHomeScreen> createState() => _KidHomeScreenState();
}

class _KidHomeScreenState extends State<KidHomeScreen> {
  bool _authenticated = false;

  @override
  void initState() {
    super.initState();
    _authenticate();
  }

  Future<void> _authenticate() async {
    final bioAuth = BiometricAuth();
    bool result = await bioAuth.authenticate(context);
    setState(() {
      _authenticated = result;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (!_authenticated) {
      return Scaffold(
        body: Center(child: Text('Authentication required to use the app.')),
      );
    }
    return Scaffold(
      appBar: AppBar(title: const Text('What do you want to buy?')),
      body: GridView.count(
        crossAxisCount: 2,
        padding: const EdgeInsets.all(24),
        children: [
          _bucketIcon('Snacks', Icons.fastfood, Colors.orange),
          _bucketIcon('School Supplies', Icons.school, Colors.blue),
          _bucketIcon('Transport', Icons.directions_bus, Colors.green),
          _bucketIcon('Other', Icons.category, Colors.purple),
        ],
      ),
    );
  }

  Widget _bucketIcon(String label, IconData icon, Color color) {
    return GestureDetector(
      onTap: () {
        // TODO: Implement payment flow for this bucket
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Selected: $label')));
      },
      child: Card(
        color: color.withOpacity(0.8),
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 64, color: Colors.white),
              SizedBox(height: 16),
              Text(label, style: TextStyle(color: Colors.white, fontSize: 20)),
            ],
          ),
        ),
      ),
    );
  }
}
