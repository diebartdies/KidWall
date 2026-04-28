import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  Future<Map<String, int>> getWalletBuckets(int parentId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/parent/$parentId/wallet_buckets'),
      headers: _token != null ? {'Authorization': 'Bearer $_token'} : {},
    );
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      if (data is Map<String, dynamic>) {
        // Expecting { 'Snacks': 120, ... }
        return data.map(
          (k, v) => MapEntry(k, v is int ? v : int.tryParse(v.toString()) ?? 0),
        );
      } else {
        return {};
      }
    } else {
      throw Exception('Failed to fetch wallet buckets: ${response.body}');
    }
  }

  Future<List<Map<String, dynamic>>> getTransactions(int childId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/child/$childId/transactions'),
      headers: _token != null ? {'Authorization': 'Bearer $_token'} : {},
    );
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      if (data is List) {
        return List<Map<String, dynamic>>.from(data);
      } else if (data is Map && data['transactions'] is List) {
        return List<Map<String, dynamic>>.from(data['transactions']);
      } else {
        return [];
      }
    } else {
      throw Exception('Failed to fetch transactions: ${response.body}');
    }
  }

  Future<List<Map<String, dynamic>>> getChildren(int parentId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/parent/$parentId/children'),
      headers: _token != null ? {'Authorization': 'Bearer $_token'} : {},
    );
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      if (data is List) {
        return List<Map<String, dynamic>>.from(data);
      } else if (data is Map && data['children'] is List) {
        return List<Map<String, dynamic>>.from(data['children']);
      } else {
        return [];
      }
    } else {
      throw Exception('Failed to fetch children: \\${response.body}');
    }
  }

  Future<Map<String, dynamic>> spendCoins({
    required int childId,
    required int merchantId,
    required double amount,
    required double payLat,
    required double payLon,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/child/spend'),
      headers: {
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      },
      body: jsonEncode({
        'child_id': childId,
        'merchant_id': merchantId,
        'amount': amount,
        'pay_lat': payLat,
        'pay_lon': payLon,
      }),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to spend coins: ${response.body}');
    }
  }

  Future<Map<String, dynamic>> register(
    String name,
    String email,
    String password,
    String role,
  ) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'name': name,
        'email': email,
        'password': password,
        'role': role,
      }),
    );
    if (response.statusCode == 200 || response.statusCode == 201) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to register');
    }
  }

  static const String baseUrl = 'https://drsrv.drsrv.net.ar:8000';
  String? _token;

  void setToken(String token) {
    _token = token;
  }

  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to login');
    }
  }

  Future<Map<String, dynamic>> get(String endpoint) async {
    final response = await http.get(
      Uri.parse('$baseUrl$endpoint'),
      headers: _token != null ? {'Authorization': 'Bearer $_token'} : {},
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('GET $endpoint failed');
    }
  }

  Future<Map<String, dynamic>> post(
    String endpoint,
    Map<String, dynamic> data,
  ) async {
    final response = await http.post(
      Uri.parse('$baseUrl$endpoint'),
      headers: {
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      },
      body: jsonEncode(data),
    );
    if (response.statusCode == 200 || response.statusCode == 201) {
      return jsonDecode(response.body);
    } else {
      throw Exception('POST $endpoint failed');
    }
  }
}
