import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
// TODO: Add Mercado Pago and Stripe SDK imports when wiring up real payment forms

class FundWalletScreen extends StatefulWidget {
  final int parentId;
  const FundWalletScreen({super.key, required this.parentId});

  @override
  State<FundWalletScreen> createState() => _FundWalletScreenState();
}

class _FundWalletScreenState extends State<FundWalletScreen> {
  final _formKey = GlobalKey<FormState>();
  final TextEditingController _amountController = TextEditingController();
  String _paymentMethod = 'mercadopago';
  bool _loading = false;
  String? _error;
  String? _success;

  // Placeholder for payment token/ID
  String? _mpToken;
  String? _stripePaymentMethodId;

  Future<void> _fundWallet() async {
    setState(() {
      _loading = true;
      _error = null;
      _success = null;
    });
    try {
      final double amount = double.parse(_amountController.text);
      final body = {
        "parent_id": widget.parentId,
        "amount_pesos": amount,
        "payment_method": _paymentMethod,
        if (_paymentMethod == 'mercadopago') "mp_token": _mpToken,
        if (_paymentMethod == 'stripe_card')
          "stripe_payment_method_id": _stripePaymentMethodId,
      };
      final response = await http.post(
        Uri.parse('https://your-backend.com/wallet/fund'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(body),
      );
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _success = data['msg'] ?? 'Wallet funded!';
        });
      } else {
        setState(() {
          _error = jsonDecode(response.body)['detail'] ?? 'Payment failed';
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Error: $e';
      });
    }
    setState(() {
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Fund Wallet')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              TextFormField(
                controller: _amountController,
                decoration: const InputDecoration(labelText: 'Amount (MXN)'),
                keyboardType: TextInputType.number,
                validator: (v) =>
                    v == null || v.isEmpty ? 'Enter amount' : null,
              ),
              DropdownButtonFormField<String>(
                value: _paymentMethod,
                items: const [
                  DropdownMenuItem(
                    value: 'mercadopago',
                    child: Text('Mercado Pago'),
                  ),
                  DropdownMenuItem(
                    value: 'stripe_card',
                    child: Text('Stripe Card'),
                  ),
                ],
                onChanged: (v) => setState(() => _paymentMethod = v!),
                decoration: const InputDecoration(labelText: 'Payment Method'),
              ),
              // TODO: Add payment forms for Mercado Pago and Stripe here
              const SizedBox(height: 24),
              if (_loading) const CircularProgressIndicator(),
              if (_error != null)
                Text(_error!, style: const TextStyle(color: Colors.red)),
              if (_success != null)
                Text(_success!, style: const TextStyle(color: Colors.green)),
              ElevatedButton(
                onPressed: _loading
                    ? null
                    : () {
                        if (_formKey.currentState!.validate()) {
                          // TODO: Collect payment token/ID before calling _fundWallet
                          _fundWallet();
                        }
                      },
                child: const Text('Fund Wallet'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
