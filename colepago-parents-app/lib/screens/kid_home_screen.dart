import 'package:flutter/material.dart';

import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../biometric_auth.dart';
import '../utils/face_obscure.dart';

class KidHomeScreen extends StatefulWidget {
  const KidHomeScreen({super.key});

  @override
  State<KidHomeScreen> createState() => _KidHomeScreenState();
}

class _KidHomeScreenState extends State<KidHomeScreen> {
  bool _obscureSensitive = false;
  bool _faceObscureEnabled =
      true; // Configurable: set to false to disable feature
  bool _authenticated = false;
  Map<String, int> _buckets = {};
  bool _loading = true;

  // Parent-configurable allowed biometrics (should be loaded from backend/settings)
  final List<BiometricTypeOption> _allowedBiometrics = [
    BiometricTypeOption.fingerprint,
    BiometricTypeOption.face,
    BiometricTypeOption.iris,
  ];

  @override
  void initState() {
    super.initState();
    _authenticate();
  }

  Future<void> _authenticate() async {
    final bioAuth = BiometricAuth();
    // In production, fetch _allowedBiometrics from parent settings/backend
    bool result = await bioAuth.authenticate(
      context,
      allowedMethods: _allowedBiometrics,
    );
    if (!mounted) return;
    setState(() {
      _authenticated = result;
    });
    if (result) {
      await _fetchBuckets();
    }
  }

  Future<void> _fetchBuckets() async {
    if (!mounted) return;
    setState(() => _loading = true);
    // Replace with your actual kid ID and backend URL
    final kidId = 456;
    final response = await http.get(
      Uri.parse('https://your-backend.com/wallet/kid/$kidId'),
    );
    if (!mounted) return;
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      setState(() {
        _buckets = {for (var b in data['buckets']) b['name']: b['coins']};
        _loading = false;
      });
    } else {
      setState(() => _loading = false);
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Failed to load buckets')));
    }
  }

  Future<void> _spendCoins(String bucket) async {
    final kidId = 456;
    final merchantId = 789; // Replace with actual merchant ID
    int maxAmount = _buckets[bucket] ?? 0;
    int totalCoins = _buckets.values.fold(0, (a, b) => a + b);

    final controller = TextEditingController();
    final amount = await showDialog<int>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Spend coins from $bucket'),
        content: TextField(
          controller: controller,
          keyboardType: TextInputType.number,
          decoration: InputDecoration(labelText: 'Amount (max $totalCoins)'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              final value = int.tryParse(controller.text);
              if (value != null && value > 0 && value <= totalCoins) {
                Navigator.of(ctx).pop(value);
              }
            },
            child: const Text('Spend'),
          ),
        ],
      ),
    );

    if (amount != null) {
      bool borrowed = false;
      Map<String, int> borrowPlan = {};
      if (amount > maxAmount) {
        // Not enough in selected bucket, but enough in total
        borrowed = true;
        // Plan: take as much as possible from the selected bucket, then from buckets with highest balance
        int needed = amount - maxAmount;
        // Sort buckets by balance descending, skip the selected bucket
        final sortedBuckets =
            _buckets.entries
                .where((e) => e.key != bucket && e.value > 0)
                .toList()
              ..sort((a, b) => b.value.compareTo(a.value));
        borrowPlan[bucket] = maxAmount;
        for (final entry in sortedBuckets) {
          if (needed <= 0) break;
          final take = entry.value >= needed ? needed : entry.value;
          borrowPlan[entry.key] = take;
          needed -= take;
        }
        // If for some reason not enough, abort
        if (needed > 0) {
          if (!mounted) return;
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Not enough coins in all buckets.')),
          );
          return;
        }
      }
      final response = await http.post(
        Uri.parse('https://your-backend.com/wallet/spend'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'kid_id': kidId,
          'bucket': bucket,
          'amount': amount,
          'merchant_id': merchantId,
          'allow_borrow': borrowed,
          if (borrowed) 'borrow_plan': borrowPlan,
        }),
      );
      if (!mounted) return;
      if (response.statusCode == 200) {
        if (borrowed) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                'Spent $amount coins (borrowed from other buckets). Parent will be notified. You will not be able to spend in the borrowing buckets until refilled.',
              ),
            ),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Spent $amount coins from $bucket!')),
          );
        }
        await _fetchBuckets();
      } else {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Failed to spend coins')));
      }
    }
  }

  Future<void> _requestMoreMoney() async {
    final kidId = 456; // Replace with actual kid ID
    final response = await http.post(
      Uri.parse('https://your-backend.com/wallet/request-more'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'kid_id': kidId,
        'channels': ['whatsapp', 'email'],
      }),
    );
    if (!mounted) return;
    if (response.statusCode == 200) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Request sent to parent via WhatsApp and email.'),
        ),
      );
    } else {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Failed to send request.')));
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_authenticated) {
      return Scaffold(
        body: Center(child: Text('Authentication required to use the app.')),
      );
    }
    if (_loading) {
      return Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    Widget content = Scaffold(
      appBar: AppBar(title: const Text('What do you want to buy?')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    icon: Icon(Icons.add_alert),
                    label: Text('Ask parent for more money'),
                    onPressed: _requestMoreMoney,
                  ),
                ),
                Switch(
                  value: _faceObscureEnabled,
                  onChanged: (v) {
                    setState(() {
                      _faceObscureEnabled = v;
                      if (!v) _obscureSensitive = false;
                    });
                  },
                  activeThumbColor: Colors.green,
                  inactiveThumbColor: Colors.red,
                  materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
                const SizedBox(width: 4),
                Text('Hide info if not alone'),
              ],
            ),
          ),
          Expanded(
            child: GridView.count(
              crossAxisCount: 2,
              padding: const EdgeInsets.all(24),
              children: _buckets.entries.map((entry) {
                final label = entry.key;
                final coins = entry.value;
                final color = _bucketColor(label);
                final icon = _bucketIconData(label);
                return _bucketIcon(label, icon, color, coins);
              }).toList(),
            ),
          ),
        ],
      ),
    );
    if (_faceObscureEnabled) {
      return FaceObscureDetector(
        onFaceDetection: (obscure) {
          if (_obscureSensitive != obscure) {
            setState(() {
              _obscureSensitive = obscure;
            });
          }
        },
        child: content,
      );
    } else {
      return content;
    }
  }

  Widget _bucketIcon(String label, IconData icon, Color color, int coins) {
    return Builder(
      builder: (context) => GestureDetector(
        onTap: () => _spendCoins(label),
        child: Card(
          color: Color.fromARGB(
            (color.a * 255.0).round().clamp(0, 255),
            (color.r * 0.8 * 255.0).round().clamp(0, 255),
            (color.g * 0.8 * 255.0).round().clamp(0, 255),
            (color.b * 0.8 * 255.0).round().clamp(0, 255),
          ),
          child: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(icon, size: 64, color: Colors.white),
                SizedBox(height: 16),
                Text(
                  obscureIfNeeded(label, _obscureSensitive),
                  style: TextStyle(color: Colors.white, fontSize: 20),
                ),
                SizedBox(height: 8),
                Text(
                  obscureIfNeeded('$coins coins', _obscureSensitive),
                  style: TextStyle(color: Colors.white, fontSize: 16),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Color _bucketColor(String label) {
    switch (label) {
      case 'Snacks':
        return Colors.orange;
      case 'School Supplies':
        return Colors.blue;
      case 'Transport':
        return Colors.green;
      case 'Other':
        return Colors.purple;
      default:
        return Colors.grey;
    }
  }

  IconData _bucketIconData(String label) {
    switch (label) {
      case 'Snacks':
        return Icons.fastfood;
      case 'School Supplies':
        return Icons.school;
      case 'Transport':
        return Icons.directions_bus;
      case 'Other':
        return Icons.category;
      default:
        return Icons.account_balance_wallet;
    }
  }
}
