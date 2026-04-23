import 'package:flutter/material.dart' as material;
import 'package:flutter/material.dart' show State, StatefulWidget;

import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:mercado_pago_ducos/mercado_pago_ducos.dart';
import 'package:dio/dio.dart';
import 'package:url_launcher/url_launcher.dart';

class FundWalletScreen extends StatefulWidget {
  final int parentId;
  const FundWalletScreen({super.key, required this.parentId});

  @override
  State<FundWalletScreen> createState() => _FundWalletScreenState();
}

class _FundWalletScreenState extends State<FundWalletScreen> {
  void _openPaymentLink() async {
    if (_mpToken != null && _mpToken!.isNotEmpty) {
      // ignore: use_build_context_synchronously
      await material.showDialog(
        context: context,
        builder: (ctx) => material.AlertDialog(
          title: const material.Text('Mercado Pago Payment Link'),
          content: material.SelectableText(_mpToken!),
          actions: [
            material.TextButton(
              onPressed: () => material.Navigator.of(ctx).pop(),
              child: const material.Text('Close'),
            ),
            material.TextButton(
              onPressed: () async {
                material.Navigator.of(ctx).pop();
                await launchUrl(Uri.parse(_mpToken!));
              },
              child: const material.Text('Open Link'),
            ),
          ],
        ),
      );
    }
  }

  final _formKey = material.GlobalKey<material.FormState>();
  final material.TextEditingController _amountController =
      material.TextEditingController();
  String _paymentMethod = 'mercadopago';
  bool _loading = false;
  String? _error;
  String? _success;

  // Placeholder for payment token/ID
  String? _mpToken;
  String? _stripePaymentMethodId;

  // Mercado Pago Ducos integration example (create preference and get init_point)
  Future<void> _getMercadoPagoToken() async {
    // Replace with your Mercado Pago access token
    const accessToken =
        'APP_USR-2764616976633952-041807-5ac6cce84579811f596731a38fa52369-3315715941';
    final dio = Dio();
    dio.options.headers['Authorization'] = 'Bearer $accessToken';
    final client = HttpClient(provider: DioHttpProvider(dio: dio));
    final mp = MercadoPago(client: client);
    try {
      final preference = await mp.createPreference(
        body: CreatePreferenceRequestBody(
          items: [
            Item(
              id: 'wallet_fund',
              title: 'Wallet Fund',
              quantity: 1,
              unitPrice: double.tryParse(_amountController.text) ?? 0,
            ),
          ],
        ),
      );
      setState(() {
        // The initPoint is the URL to redirect the user to complete the payment
        _mpToken = preference.initPoint;
        _error = null;
      });
    } catch (e) {
      setState(() {
        _error = 'Mercado Pago error: $e';
      });
    }
  }

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
  material.Widget build(material.BuildContext context) {
    // Responsive layout: center content and constrain max width for tablet/desktop
    final double maxFormWidth = 400;
    return material.Scaffold(
      appBar: material.AppBar(title: const material.Text('Fund Wallet')),
      body: material.Center(
        child: material.SingleChildScrollView(
          child: material.ConstrainedBox(
            constraints: material.BoxConstraints(maxWidth: maxFormWidth),
            child: material.Card(
              elevation: 4,
              shape: material.RoundedRectangleBorder(
                borderRadius: material.BorderRadius.circular(16),
              ),
              child: material.Padding(
                padding: const material.EdgeInsets.all(24.0),
                child: material.Form(
                  key: _formKey,
                  child: material.Column(
                    mainAxisSize: material.MainAxisSize.min,
                    crossAxisAlignment: material.CrossAxisAlignment.stretch,
                    children: [
                      material.Text(
                        'Fund Your Wallet',
                        style: material.Theme.of(context)
                            .textTheme
                            .headlineSmall
                            ?.copyWith(fontWeight: material.FontWeight.bold),
                        textAlign: material.TextAlign.center,
                      ),
                      const material.SizedBox(height: 24),
                      material.TextFormField(
                        controller: _amountController,
                        decoration: const material.InputDecoration(
                          labelText: 'Amount (MXN)',
                          prefixIcon: material.Icon(
                            material.Icons.attach_money,
                          ),
                          border: material.OutlineInputBorder(),
                        ),
                        keyboardType: material.TextInputType.number,
                        validator: (v) =>
                            v == null || v.isEmpty ? 'Enter amount' : null,
                      ),
                      const material.SizedBox(height: 16),
                      material.DropdownButtonFormField<String>(
                        initialValue: _paymentMethod,
                        items: [
                          material.DropdownMenuItem(
                            value: 'mercadopago',
                            child: material.Row(
                              children: [
                                material.Image.network(
                                  'https://seeklogo.com/images/M/mercado-pago-logo-7B1C0B7B0B-seeklogo.com.png',
                                  width: 24,
                                  height: 24,
                                  errorBuilder: (c, e, s) =>
                                      const material.Icon(
                                        material.Icons.account_balance_wallet,
                                      ),
                                ),
                                const material.SizedBox(width: 8),
                                const material.Text('Mercado Pago'),
                              ],
                            ),
                          ),
                          material.DropdownMenuItem(
                            value: 'stripe_card',
                            child: material.Row(
                              children: [
                                material.Image.network(
                                  'https://seeklogo.com/images/S/stripe-logo-660F8FEC34-seeklogo.com.png',
                                  width: 24,
                                  height: 24,
                                  errorBuilder: (c, e, s) =>
                                      const material.Icon(
                                        material.Icons.credit_card,
                                      ),
                                ),
                                const material.SizedBox(width: 8),
                                const material.Text('Stripe Card'),
                              ],
                            ),
                          ),
                        ],
                        onChanged: (v) => setState(() => _paymentMethod = v!),
                        decoration: const material.InputDecoration(
                          labelText: 'Payment Method',
                          border: material.OutlineInputBorder(),
                        ),
                      ),
                      const material.SizedBox(height: 16),
                      if (_paymentMethod == 'mercadopago')
                        material.Row(
                          children: [
                            material.Expanded(
                              child: material.TextFormField(
                                decoration: const material.InputDecoration(
                                  labelText: 'Mercado Pago Payment Link',
                                  prefixIcon: material.Icon(
                                    material.Icons.vpn_key,
                                  ),
                                  border: material.OutlineInputBorder(),
                                ),
                                controller: material.TextEditingController(
                                  text: _mpToken,
                                ),
                                onChanged: (v) => _mpToken = v,
                                validator: (v) =>
                                    _paymentMethod == 'mercadopago' &&
                                        (v == null || v.isEmpty)
                                    ? 'Get the Mercado Pago payment link'
                                    : null,
                              ),
                            ),
                            material.SizedBox(width: 8),
                            material.ElevatedButton(
                              onPressed: _loading ? null : _getMercadoPagoToken,
                              child: const material.Text('Get Link'),
                            ),
                            if (_mpToken != null && _mpToken!.isNotEmpty)
                              material.SizedBox(width: 8),
                            if (_mpToken != null && _mpToken!.isNotEmpty)
                              material.ElevatedButton(
                                onPressed: _openPaymentLink,
                                child: const material.Text('Open'),
                              ),
                          ],
                        ),
                      if (_paymentMethod == 'stripe_card')
                        material.TextFormField(
                          decoration: const material.InputDecoration(
                            labelText: 'Stripe Payment Method ID',
                            prefixIcon: material.Icon(
                              material.Icons.credit_card,
                            ),
                            border: material.OutlineInputBorder(),
                          ),
                          onChanged: (v) => _stripePaymentMethodId = v,
                          validator: (v) =>
                              _paymentMethod == 'stripe_card' &&
                                  (v == null || v.isEmpty)
                              ? 'Enter Stripe Payment Method ID'
                              : null,
                        ),
                      const material.SizedBox(height: 24),
                      if (_loading) ...[
                        const material.Center(
                          child: material.CircularProgressIndicator(),
                        ),
                        const material.SizedBox(height: 16),
                      ],
                      if (_error != null)
                        material.Text(
                          _error!,
                          style: const material.TextStyle(
                            color: material.Colors.red,
                          ),
                          textAlign: material.TextAlign.center,
                        ),
                      if (_success != null)
                        material.Text(
                          _success!,
                          style: const material.TextStyle(
                            color: material.Colors.green,
                          ),
                          textAlign: material.TextAlign.center,
                        ),
                      const material.SizedBox(height: 16),
                      material.SizedBox(
                        width: double.infinity,
                        child: material.ElevatedButton.icon(
                          icon: const material.Icon(
                            material.Icons.account_balance_wallet,
                          ),
                          label: const material.Text('Fund Wallet'),
                          style: material.ElevatedButton.styleFrom(
                            padding: const material.EdgeInsets.symmetric(
                              vertical: 16,
                            ),
                            textStyle: const material.TextStyle(fontSize: 18),
                          ),
                          onPressed: _loading
                              ? null
                              : () {
                                  if (_formKey.currentState!.validate()) {
                                    if ((_paymentMethod == 'mercadopago' &&
                                            (_mpToken == null ||
                                                _mpToken!.isEmpty)) ||
                                        (_paymentMethod == 'stripe_card' &&
                                            (_stripePaymentMethodId == null ||
                                                _stripePaymentMethodId!
                                                    .isEmpty))) {
                                      setState(() {
                                        _error =
                                            'Please provide a valid payment token or ID.';
                                      });
                                      return;
                                    }
                                    _fundWallet();
                                  }
                                },
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
