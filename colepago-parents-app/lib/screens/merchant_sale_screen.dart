import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../api_service.dart';

class MerchantSaleScreen extends StatefulWidget {
  final String token;
  final int merchantId;

  const MerchantSaleScreen({
    super.key,
    required this.token,
    required this.merchantId,
  });

  @override
  State<MerchantSaleScreen> createState() => _MerchantSaleScreenState();
}

class _MerchantSaleScreenState extends State<MerchantSaleScreen> {
  static const _bucketNames = [
    'Lunch / Snacks',
    'Books',
    'Fotocopies',
    'Transport',
    'General',
  ];

  final ApiService _api = ApiService();
  final List<_SaleItemDraft> _items = [_SaleItemDraft()];
  final _noteCtrl = TextEditingController();
  String? _payload;
  double _total = 0;
  bool _creating = false;

  @override
  void initState() {
    super.initState();
    _api.setToken(widget.token);
  }

  @override
  void dispose() {
    for (final item in _items) {
      item.dispose();
    }
    _noteCtrl.dispose();
    super.dispose();
  }

  void _recalculate() {
    setState(() {
      _total = _items.fold<double>(0, (sum, item) => sum + item.total);
      _payload = null;
    });
  }

  Future<void> _createQrPayload() async {
    final items = _items
        .where((item) => item.description.trim().isNotEmpty)
        .map((item) => item.toJson())
        .toList();
    if (items.isEmpty) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Add at least one item')));
      return;
    }
    setState(() => _creating = true);
    try {
      final response = await _api.createMerchantSaleQr(
        merchantId: widget.merchantId,
        items: items,
        note: _noteCtrl.text.trim(),
      );
      setState(() {
        _payload = response['qr_payload']?.toString();
        _total = _asDouble(response['sale']?['total']);
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
      );
    } finally {
      if (mounted) setState(() => _creating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('New Sale')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            'Enter each sold item and the bucket it should affect. ColePago calculates the total and creates the QR the kid scans from the chosen bucket.',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: 16),
          ..._items.asMap().entries.map((entry) {
            return _itemEditor(entry.key, entry.value);
          }),
          OutlinedButton.icon(
            icon: const Icon(Icons.add),
            label: const Text('Add Item'),
            onPressed: () {
              setState(() => _items.add(_SaleItemDraft()));
            },
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _noteCtrl,
            decoration: const InputDecoration(
              labelText: 'Sale note',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          Text(
            'Total: ${_total.toStringAsFixed(2)}',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            icon: _creating
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.qr_code),
            label: const Text('Sell and Show QR'),
            onPressed: _creating ? null : _createQrPayload,
          ),
          if (_payload != null) ...[
            const SizedBox(height: 18),
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                border: Border.all(color: Colors.blueAccent),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                children: [
                  QrImageView(
                    data: _payload!,
                    version: QrVersions.auto,
                    size: 240,
                    backgroundColor: Colors.white,
                  ),
                  const SizedBox(height: 8),
                  const Text('ColePago Sale QR'),
                  const SizedBox(height: 4),
                  const Text('Show this code to the kid camera.'),
                  const SizedBox(height: 12),
                  SelectableText(_payload!),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _itemEditor(int index, _SaleItemDraft item) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            TextField(
              controller: item.descriptionCtrl,
              decoration: InputDecoration(
                labelText: 'Item ${index + 1} description',
              ),
              onChanged: (_) => _recalculate(),
            ),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              initialValue: item.bucketName,
              decoration: const InputDecoration(
                labelText: 'Bucket impacted',
                border: OutlineInputBorder(),
              ),
              items: _bucketNames
                  .map(
                    (name) => DropdownMenuItem(value: name, child: Text(name)),
                  )
                  .toList(),
              onChanged: (value) {
                setState(() {
                  item.bucketName = value ?? 'General';
                  _payload = null;
                });
              },
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: item.quantityCtrl,
                    keyboardType: const TextInputType.numberWithOptions(
                      decimal: true,
                    ),
                    decoration: const InputDecoration(labelText: 'Quantity'),
                    onChanged: (_) => _recalculate(),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextField(
                    controller: item.priceCtrl,
                    keyboardType: const TextInputType.numberWithOptions(
                      decimal: true,
                    ),
                    decoration: const InputDecoration(labelText: 'Price'),
                    onChanged: (_) => _recalculate(),
                  ),
                ),
              ],
            ),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton.icon(
                icon: const Icon(Icons.delete),
                label: const Text('Remove'),
                onPressed: _items.length == 1
                    ? null
                    : () {
                        final removed = _items.removeAt(index);
                        removed.dispose();
                        setState(() {
                          _total = _items.fold<double>(
                            0,
                            (sum, item) => sum + item.total,
                          );
                          _payload = null;
                        });
                      },
              ),
            ),
          ],
        ),
      ),
    );
  }

  double _asDouble(dynamic value) {
    if (value is num) return value.toDouble();
    return double.tryParse(value?.toString() ?? '') ?? 0;
  }
}

class _SaleItemDraft {
  final descriptionCtrl = TextEditingController();
  final quantityCtrl = TextEditingController(text: '1');
  final priceCtrl = TextEditingController();
  String bucketName = 'General';

  String get description => descriptionCtrl.text;
  double get quantity => double.tryParse(quantityCtrl.text.trim()) ?? 0;
  double get price => double.tryParse(priceCtrl.text.trim()) ?? 0;
  double get total => quantity * price;

  Map<String, dynamic> toJson() => {
    'description': description.trim(),
    'quantity': quantity,
    'unit_price': price,
    'bucket_name': bucketName,
  };

  void dispose() {
    descriptionCtrl.dispose();
    quantityCtrl.dispose();
    priceCtrl.dispose();
  }
}
