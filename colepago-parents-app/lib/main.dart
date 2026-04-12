import 'package:flutter/material.dart';
import 'screens/login_screen.dart';
import 'screens/kid_home_screen.dart';
import 'screens/fund_wallet_screen.dart';

const String appFlavor = String.fromEnvironment('FLAVOR', defaultValue: 'kids');

void main() {
  runApp(ColePagoApp());
}

class ColePagoApp extends StatelessWidget {
  const ColePagoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: appFlavor == 'parents' ? 'ColePago Parents' : 'ColePago Kids',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blueAccent),
        useMaterial3: true,
      ),
      home: appFlavor == 'parents'
          ? const MainDrawerScaffold()
          : const KidHomeScreen(),
    );
  }
}

class MainDrawerScaffold extends StatefulWidget {
  const MainDrawerScaffold({super.key});

  @override
  State<MainDrawerScaffold> createState() => _MainDrawerScaffoldState();
}

class _MainDrawerScaffoldState extends State<MainDrawerScaffold> {
  int _selectedIndex = 0;
  String? _token;

  final List<String> _titles = [
    'Dashboard',
    'Fund Wallet',
    'Buckets',
    'Transactions',
    'Notifications',
    'Settings',
    'Login',
  ];

  void _onSelect(int index) {
    setState(() {
      _selectedIndex = index;
      Navigator.pop(context); // close drawer
    });
  }

  void _onLoginSuccess(String token) {
    setState(() {
      _token = token;
      _selectedIndex = 0; // Go to dashboard
    });
  }

  List<Widget> get _screens => [
    Center(
      child: Text(
        _token != null ? 'Dashboard: Child Wallets & Balances' : 'Please login',
      ),
    ), // 0
    _token != null
        ? FundWalletScreen(
            parentId: 1,
          ) // TODO: Replace with actual parent ID from login/session
        : Center(child: Text('Please login to fund wallet')), // 1
    Center(child: Text('Buckets Management')), // 2
    Center(child: Text('Transaction History')), // 3
    Center(child: Text('Notifications')), // 4
    Center(child: Text('Settings (Language, Terms, Commission)')), // 5
    _token == null
        ? LoginScreen(onLoginSuccess: _onLoginSuccess)
        : Center(child: Text('Already logged in')), // 6
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_titles[_selectedIndex])),
      drawer: Drawer(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            DrawerHeader(
              decoration: BoxDecoration(color: Colors.blueAccent),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.account_balance_wallet,
                    size: 48,
                    color: Colors.white,
                  ),
                  SizedBox(height: 8),
                  Text(
                    'ColePago Parents',
                    style: TextStyle(color: Colors.white, fontSize: 20),
                  ),
                ],
              ),
            ),
            ListTile(
              leading: Icon(Icons.dashboard),
              title: Text('Dashboard'),
              onTap: () => _onSelect(0),
            ),
            ListTile(
              leading: Icon(Icons.account_balance),
              title: Text('Fund Wallet'),
              onTap: () => _onSelect(1),
            ),
            ListTile(
              leading: Icon(Icons.category),
              title: Text('Buckets'),
              onTap: () => _onSelect(2),
            ),
            ListTile(
              leading: Icon(Icons.history),
              title: Text('Transactions'),
              onTap: () => _onSelect(3),
            ),
            ListTile(
              leading: Icon(Icons.notifications),
              title: Text('Notifications'),
              onTap: () => _onSelect(4),
            ),
            ListTile(
              leading: Icon(Icons.settings),
              title: Text('Settings'),
              onTap: () => _onSelect(5),
            ),
            Divider(),
            ListTile(
              leading: Icon(Icons.login),
              title: Text(_token == null ? 'Login / Register' : 'Logout'),
              onTap: () {
                if (_token == null) {
                  _onSelect(6);
                } else {
                  setState(() {
                    _token = null;
                    _selectedIndex = 6;
                  });
                }
              },
            ),
          ],
        ),
      ),
      body: _screens[_selectedIndex],
    );
  }
}
