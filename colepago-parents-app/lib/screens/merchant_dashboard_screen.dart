import 'package:flutter/material.dart';
import 'merchant_profile_form_screen.dart';
import 'merchant_sale_screen.dart';

class MerchantDashboardScreen extends StatelessWidget {
  final String token;
  final int merchantId;

  const MerchantDashboardScreen({
    super.key,
    required this.token,
    required this.merchantId,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Merchant Dashboard')),
      drawer: Drawer(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            const DrawerHeader(
              decoration: BoxDecoration(color: Colors.blueAccent),
              child: Text(
                'Merchant',
                style: TextStyle(color: Colors.white, fontSize: 24),
              ),
            ),
            ListTile(
              leading: const Icon(Icons.qr_code),
              title: const Text('New Sale'),
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => MerchantSaleScreen(
                      token: token,
                      merchantId: merchantId,
                    ),
                  ),
                );
              },
            ),
            ListTile(
              leading: const Icon(Icons.storefront),
              title: const Text('Merchant Information'),
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => MerchantProfileFormScreen(
                      token: token,
                      merchantId: merchantId,
                    ),
                  ),
                );
              },
            ),
          ],
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'Receivables and payout tools will appear here.',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              icon: const Icon(Icons.qr_code),
              label: const Text('Create Sale QR'),
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => MerchantSaleScreen(
                      token: token,
                      merchantId: merchantId,
                    ),
                  ),
                );
              },
            ),
            const SizedBox(height: 12),
            ElevatedButton.icon(
              icon: const Icon(Icons.storefront),
              label: const Text('Complete Merchant Information'),
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => MerchantProfileFormScreen(
                      token: token,
                      merchantId: merchantId,
                    ),
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
