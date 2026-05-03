import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String _githubApiBaseUrl = 'https://api.github.com';

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

  Future<Map<String, dynamic>> importGithubRepoInfo({
    required String owner,
    required String repo,
    String? githubToken,
  }) async {
    final response = await http.get(
      Uri.parse('$_githubApiBaseUrl/repos/$owner/$repo'),
      headers: {
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        if (githubToken != null && githubToken.isNotEmpty)
          'Authorization': 'Bearer $githubToken',
      },
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to import GitHub repo info: ${response.body}');
    }

    final data = jsonDecode(response.body);
    if (data is! Map<String, dynamic>) {
      throw Exception('Unexpected GitHub response format for repository info');
    }

    return {
      'id': data['id'],
      'name': data['name'],
      'full_name': data['full_name'],
      'private': data['private'],
      'description': data['description'],
      'default_branch': data['default_branch'],
      'html_url': data['html_url'],
      'stargazers_count': data['stargazers_count'],
      'watchers_count': data['watchers_count'],
      'forks_count': data['forks_count'],
      'open_issues_count': data['open_issues_count'],
      'updated_at': data['updated_at'],
      'owner': data['owner'] is Map<String, dynamic>
          ? {
              'login': data['owner']['login'],
              'id': data['owner']['id'],
              'avatar_url': data['owner']['avatar_url'],
            }
          : null,
    };
  }

  Future<List<Map<String, dynamic>>> importGithubIssues({
    required String owner,
    required String repo,
    String state = 'open',
    int perPage = 30,
    String? githubToken,
  }) async {
    final response = await http.get(
      Uri.parse(
        '$_githubApiBaseUrl/repos/$owner/$repo/issues?state=$state&per_page=$perPage',
      ),
      headers: {
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        if (githubToken != null && githubToken.isNotEmpty)
          'Authorization': 'Bearer $githubToken',
      },
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to import GitHub issues: ${response.body}');
    }

    final data = jsonDecode(response.body);
    if (data is! List) {
      throw Exception('Unexpected GitHub response format for issues');
    }

    return data
        .whereType<Map<String, dynamic>>()
        // Filter out pull requests to keep only issues.
        .where((item) => item['pull_request'] == null)
        .map(
          (item) => {
            'id': item['id'],
            'number': item['number'],
            'title': item['title'],
            'state': item['state'],
            'created_at': item['created_at'],
            'updated_at': item['updated_at'],
            'html_url': item['html_url'],
            'user': item['user'] is Map<String, dynamic>
                ? {'login': item['user']['login'], 'id': item['user']['id']}
                : null,
          },
        )
        .toList();
  }
}
