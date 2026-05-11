import 'package:flutter/material.dart';
import 'fund_wallet_screen.dart';
import 'add_child_screen.dart';
import 'parent_profile_form_screen.dart';
import '../api_service.dart';

class ParentDashboardScreen extends StatefulWidget {
  final String token;
  final int parentId;
  const ParentDashboardScreen({
    super.key,
    required this.token,
    required this.parentId,
  });

  @override
  State<ParentDashboardScreen> createState() => _ParentDashboardScreenState();
}

class _ParentDashboardScreenState extends State<ParentDashboardScreen> {
  List<Map<String, dynamic>> children = [];
  Map<String, int> walletBuckets = {};
  List<Map<String, dynamic>> transactions = [];
  int? selectedChildId;
  bool loading = true;
  final ApiService _apiService = ApiService();

  @override
  void initState() {
    super.initState();
    _apiService.setToken(widget.token);
    _fetchDashboardData();
  }

  Future<void> _fetchDashboardData() async {
    setState(() {
      loading = true;
    });
    try {
      final fetchedChildren = await _apiService.getChildren(widget.parentId);
      Map<String, int> fetchedWalletBuckets = {};
      List<Map<String, dynamic>> fetchedTransactions = [];
      int? firstChildId = fetchedChildren.isNotEmpty
          ? fetchedChildren.first['id']
          : null;
      if (firstChildId != null) {
        fetchedWalletBuckets = await _apiService.getWalletBuckets(
          widget.parentId,
        );
        fetchedTransactions = (await _apiService.getTransactions(
          firstChildId,
        )).cast<Map<String, dynamic>>();
      }
      setState(() {
        children = fetchedChildren;
        selectedChildId = firstChildId;
        walletBuckets = fetchedWalletBuckets;
        transactions = fetchedTransactions;
        loading = false;
      });
    } catch (e) {
      setState(() {
        children = [];
        selectedChildId = null;
        walletBuckets = {};
        transactions = [];
        loading = false;
      });
      // Optionally show error
      // ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to load dashboard data')));
    }
  }

  @override
  Widget build(BuildContext context) {
    // Ensure c['id'] is unique for each child (debug only)
    assert(
      children.map((c) => c['id'] as int).toSet().length == children.length,
      'Each child id must be unique.',
    );
    return Scaffold(
      appBar: AppBar(title: const Text('Parent Dashboard')),
      drawer: Drawer(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            const DrawerHeader(
              decoration: BoxDecoration(color: Colors.blueAccent),
              child: Text(
                'Menu',
                style: TextStyle(color: Colors.white, fontSize: 24),
              ),
            ),
            ListTile(
              leading: const Icon(Icons.settings),
              title: const Text('Parent Config'),
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => ParentProfileFormScreen(
                      token: widget.token,
                      parentId: widget.parentId,
                    ),
                  ),
                );
              },
            ),
            ListTile(
              leading: const Icon(Icons.child_care),
              title: const Text('Manage Children'),
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => AddChildScreen(
                      token: widget.token,
                      parentId: widget.parentId,
                    ),
                  ),
                );
              },
            ),
            ListTile(
              leading: const Icon(Icons.account_balance_wallet),
              title: const Text('Add Credit'),
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) =>
                        FundWalletScreen(parentId: widget.parentId),
                  ),
                );
              },
            ),
          ],
        ),
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Wallet buckets
                  Text(
                    'Wallet Balance per Bucket',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 8),
                  SizedBox(
                    height: 80,
                    child: ListView(
                      scrollDirection: Axis.horizontal,
                      children: walletBuckets.entries
                          .map(
                            (e) => Card(
                              margin: const EdgeInsets.symmetric(horizontal: 8),
                              child: Container(
                                width: 120,
                                padding: const EdgeInsets.all(12),
                                child: Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Text(
                                      e.key,
                                      style: const TextStyle(
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                    const SizedBox(height: 8),
                                    Text(
                                      '${e.value} MXN',
                                      style: const TextStyle(fontSize: 18),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          )
                          .toList(),
                    ),
                  ),
                  const SizedBox(height: 24),
                  // Children dropdown
                  if (children.isEmpty) ...[
                    const SizedBox(height: 24),
                    Center(
                      child: Column(
                        children: [
                          Text(
                            'No children found. Please add at least one child to view wallet and transactions.',
                            style: TextStyle(color: Colors.red, fontSize: 16),
                            textAlign: TextAlign.center,
                          ),
                          const SizedBox(height: 16),
                          ElevatedButton.icon(
                            icon: const Icon(Icons.child_care),
                            label: const Text('Add Child'),
                            onPressed: () {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (context) => AddChildScreen(
                                    token: widget.token,
                                    parentId: widget.parentId,
                                  ),
                                ),
                              );
                            },
                          ),
                        ],
                      ),
                    ),
                  ] else ...[
                    Row(
                      children: [
                        const Text('Child: '),
                        DropdownButton<int>(
                          value: selectedChildId,
                          items: children
                              .map(
                                (c) => DropdownMenuItem(
                                  value: c['id'] as int,
                                  child: Text(c['name']),
                                ),
                              )
                              .toList(),
                          onChanged: (id) async {
                            setState(() {
                              selectedChildId = id;
                              loading = true;
                            });
                            try {
                              final fetchedTransactions = id != null
                                  ? (await _apiService.getTransactions(
                                      id,
                                    )).cast<Map<String, dynamic>>()
                                  : <Map<String, dynamic>>[];
                              setState(() {
                                transactions = fetchedTransactions;
                                loading = false;
                              });
                            } catch (e) {
                              setState(() {
                                transactions = [];
                                loading = false;
                              });
                            }
                          },
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    // Recent transactions
                    Text(
                      'Recent Transactions',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 8),
                    Expanded(
                      child: ListView(
                        children: transactions
                            .where((t) => t['childId'] == selectedChildId)
                            .map(
                              (t) => ListTile(
                                leading: Icon(
                                  t['amount'] > 0 ? Icons.add : Icons.remove,
                                  color: t['amount'] > 0
                                      ? Colors.green
                                      : Colors.red,
                                ),
                                title: Text(t['desc']),
                                subtitle: Text(t['date']),
                                trailing: Text('${t['amount']} MXN'),
                              ),
                            )
                            .toList(),
                      ),
                    ),
                  ],
                ],
              ),
            ),
    );
  }
}
