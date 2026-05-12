import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../biometric_auth.dart';
import '../api_service.dart';
import '../utils/face_obscure.dart';

class KidHomeScreen extends StatefulWidget {
  final String token;
  final int kidId;

  const KidHomeScreen({super.key, required this.token, required this.kidId});

  @override
  State<KidHomeScreen> createState() => _KidHomeScreenState();
}

class _KidHomeScreenState extends State<KidHomeScreen> {
  final ApiService _api = ApiService();
  final List<BiometricTypeOption> _allowedBiometrics = [
    BiometricTypeOption.fingerprint,
    BiometricTypeOption.face,
    BiometricTypeOption.iris,
  ];

  bool _authenticated = false;
  bool _loading = true;
  bool _faceObscureEnabled = true;
  bool _obscureSensitive = false;
  List<Map<String, dynamic>> _buckets = [];
  String _backgroundId = 'sky';

  static const List<_KidBackground> _backgrounds = [
    _KidBackground(
      id: 'sky',
      name: 'Sky',
      icon: Icons.wb_sunny,
      colors: [Color(0xFF7DD3FC), Color(0xFFFFF7AD)],
    ),
    _KidBackground(
      id: 'space',
      name: 'Space',
      icon: Icons.rocket_launch,
      colors: [Color(0xFF312E81), Color(0xFF7C3AED)],
      darkText: false,
    ),
    _KidBackground(
      id: 'candy',
      name: 'Candy',
      icon: Icons.icecream,
      colors: [Color(0xFFFF8BC7), Color(0xFFFFD166)],
    ),
    _KidBackground(
      id: 'jungle',
      name: 'Jungle',
      icon: Icons.park,
      colors: [Color(0xFF34D399), Color(0xFFA7F3D0)],
    ),
    _KidBackground(
      id: 'arcade',
      name: 'Arcade',
      icon: Icons.sports_esports,
      colors: [Color(0xFF06B6D4), Color(0xFF2563EB)],
      darkText: false,
    ),
  ];

  @override
  void initState() {
    super.initState();
    _api.setToken(widget.token);
    _loadBackground();
    _authenticate();
  }

  _KidBackground get _selectedBackground => _backgrounds.firstWhere(
    (background) => background.id == _backgroundId,
    orElse: () => _backgrounds.first,
  );

  String get _backgroundPrefsKey => 'kidBackground:${widget.kidId}';

  Future<void> _loadBackground() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_backgroundPrefsKey);
    if (!mounted || saved == null) return;
    if (_backgrounds.any((background) => background.id == saved)) {
      setState(() => _backgroundId = saved);
    }
  }

  Future<void> _saveBackground(String id) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_backgroundPrefsKey, id);
    if (!mounted) return;
    setState(() => _backgroundId = id);
  }

  Future<void> _authenticate() async {
    final result = await BiometricAuth().authenticate(
      context,
      allowedMethods: _allowedBiometrics,
    );
    if (!mounted) return;
    setState(() => _authenticated = result);
    if (result) await _fetchBuckets();
  }

  Future<void> _fetchBuckets() async {
    setState(() => _loading = true);
    try {
      final buckets = await _api.getChildWalletBuckets(widget.kidId);
      if (!mounted) return;
      setState(() {
        _buckets = buckets;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _loading = false);
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Failed to load buckets')));
    }
  }

  Future<void> _openSaleScanner(Map<String, dynamic> bucket) async {
    final paid = await Navigator.push<bool>(
      context,
      MaterialPageRoute(
        builder: (_) => KidSaleScannerScreen(
          api: _api,
          childId: widget.kidId,
          bucketName: bucket['name']?.toString() ?? '',
        ),
      ),
    );
    if (paid == true) await _fetchBuckets();
  }

  @override
  Widget build(BuildContext context) {
    if (!_authenticated) {
      return Scaffold(
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.lock, size: 48),
              const SizedBox(height: 12),
              const Text('Secure access required'),
              const SizedBox(height: 12),
              ElevatedButton(
                onPressed: _authenticate,
                child: const Text('Try again'),
              ),
            ],
          ),
        ),
      );
    }

    final background = _selectedBackground;
    final content = Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: const Text('Choose a bucket'),
        backgroundColor: background.appBarColor,
        foregroundColor: background.darkText ? Colors.black87 : Colors.white,
        actions: [
          IconButton(
            tooltip: 'Change background',
            icon: const Icon(Icons.palette),
            onPressed: _showBackgroundPicker,
          ),
        ],
      ),
      body: DecoratedBox(
        decoration: background.decoration,
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.fromLTRB(12, 12, 12, 0),
                    child: Card(
                      color: background.panelColor,
                      child: SwitchListTile(
                        title: const Text(
                          'Hide info if another face is detected',
                        ),
                        value: _faceObscureEnabled,
                        onChanged: (value) {
                          setState(() {
                            _faceObscureEnabled = value;
                            if (!value) _obscureSensitive = false;
                          });
                        },
                      ),
                    ),
                  ),
                  Expanded(
                    child: GridView.count(
                      crossAxisCount: 2,
                      padding: const EdgeInsets.all(16),
                      children: _buckets.map((bucket) {
                        final name = bucket['name']?.toString() ?? 'Bucket';
                        final remaining = _asDouble(bucket['remaining']);
                        return _bucketCard(name, remaining, bucket);
                      }).toList(),
                    ),
                  ),
                ],
              ),
      ),
    );

    if (!_faceObscureEnabled) return content;
    return FaceObscureDetector(
      onFaceDetection: (obscure) {
        if (_obscureSensitive != obscure) {
          setState(() => _obscureSensitive = obscure);
        }
      },
      child: content,
    );
  }

  Widget _bucketCard(
    String name,
    double remaining,
    Map<String, dynamic> bucket,
  ) {
    final color = _bucketColor(name);
    return Card(
      color: color,
      child: InkWell(
        onTap: remaining <= 0 ? null : () => _openSaleScanner(bucket),
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(_bucketIconData(name), size: 52, color: Colors.white),
              const SizedBox(height: 12),
              Text(
                obscureIfNeeded(name, _obscureSensitive),
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                obscureIfNeeded(
                  remaining.toStringAsFixed(2),
                  _obscureSensitive,
                ),
                style: const TextStyle(color: Colors.white),
              ),
              const SizedBox(height: 8),
              const Icon(Icons.qr_code_scanner, color: Colors.white),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _showBackgroundPicker() async {
    final selected = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (context) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 18),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Pick a background',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 14),
                GridView.count(
                  shrinkWrap: true,
                  crossAxisCount: 2,
                  childAspectRatio: 2.6,
                  mainAxisSpacing: 10,
                  crossAxisSpacing: 10,
                  children: _backgrounds.map((background) {
                    final selected = background.id == _backgroundId;
                    return InkWell(
                      borderRadius: BorderRadius.circular(12),
                      onTap: () => Navigator.pop(context, background.id),
                      child: DecoratedBox(
                        decoration: BoxDecoration(
                          gradient: LinearGradient(colors: background.colors),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(
                            color: selected
                                ? Theme.of(context).colorScheme.primary
                                : Colors.transparent,
                            width: 3,
                          ),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              background.icon,
                              color: background.darkText
                                  ? Colors.black87
                                  : Colors.white,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              background.name,
                              style: TextStyle(
                                color: background.darkText
                                    ? Colors.black87
                                    : Colors.white,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ],
            ),
          ),
        );
      },
    );
    if (selected != null) await _saveBackground(selected);
  }

  double _asDouble(dynamic value) {
    if (value is num) return value.toDouble();
    return double.tryParse(value?.toString() ?? '') ?? 0;
  }

  Color _bucketColor(String label) {
    if (label.toLowerCase().contains('snack') ||
        label.toLowerCase().contains('lunch')) {
      return Colors.orange;
    }
    if (label.toLowerCase().contains('book')) return Colors.indigo;
    if (label.toLowerCase().contains('transport')) return Colors.green;
    if (label.toLowerCase().contains('foto')) return Colors.purple;
    return Colors.blueGrey;
  }

  IconData _bucketIconData(String label) {
    if (label.toLowerCase().contains('snack') ||
        label.toLowerCase().contains('lunch')) {
      return Icons.fastfood;
    }
    if (label.toLowerCase().contains('book')) return Icons.menu_book;
    if (label.toLowerCase().contains('transport')) {
      return Icons.directions_bus;
    }
    if (label.toLowerCase().contains('foto')) return Icons.print;
    return Icons.account_balance_wallet;
  }
}

class _KidBackground {
  final String id;
  final String name;
  final IconData icon;
  final List<Color> colors;
  final bool darkText;

  const _KidBackground({
    required this.id,
    required this.name,
    required this.icon,
    required this.colors,
    this.darkText = true,
  });

  BoxDecoration get decoration {
    return BoxDecoration(
      gradient: LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: colors,
      ),
    );
  }

  Color get appBarColor => colors.first.withAlpha(230);

  Color get panelColor =>
      darkText ? const Color(0xE6FFFFFF) : const Color(0xD91F2937);
}

class KidSaleScannerScreen extends StatefulWidget {
  final ApiService api;
  final int childId;
  final String bucketName;

  const KidSaleScannerScreen({
    super.key,
    required this.api,
    required this.childId,
    required this.bucketName,
  });

  @override
  State<KidSaleScannerScreen> createState() => _KidSaleScannerScreenState();
}

class _KidSaleScannerScreenState extends State<KidSaleScannerScreen> {
  final MobileScannerController _scannerController = MobileScannerController();
  bool _paying = false;

  @override
  void dispose() {
    _scannerController.dispose();
    super.dispose();
  }

  void _onDetect(BarcodeCapture capture) {
    if (_paying) return;
    String? payload;
    for (final barcode in capture.barcodes) {
      final value = barcode.rawValue;
      if (value != null && value.trim().isNotEmpty) {
        payload = value.trim();
        break;
      }
    }
    if (payload == null) return;
    _pay(payload);
  }

  Future<void> _pay(String scannedPayload) async {
    final payload = scannedPayload.trim();
    if (payload.isEmpty) return;
    setState(() => _paying = true);
    await _scannerController.stop();
    try {
      await widget.api.payMerchantSale(
        childId: widget.childId,
        bucketName: widget.bucketName,
        salePayload: payload,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Payment processed')));
      Navigator.pop(context, true);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
      );
      await _scannerController.start();
    } finally {
      if (mounted) setState(() => _paying = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Scan sale - ${widget.bucketName}')),
      body: Column(
        children: [
          Expanded(
            child: Container(
              clipBehavior: Clip.antiAlias,
              decoration: const BoxDecoration(color: Colors.black87),
              child: Stack(
                fit: StackFit.expand,
                children: [
                  MobileScanner(
                    controller: _scannerController,
                    onDetect: _onDetect,
                  ),
                  if (_paying)
                    Container(
                      color: Colors.black54,
                      alignment: Alignment.center,
                      child: const CircularProgressIndicator(),
                    ),
                ],
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                const Icon(Icons.qr_code_scanner),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    _paying
                        ? 'Processing secure payment...'
                        : 'Point the camera at the merchant ColePago QR.',
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
