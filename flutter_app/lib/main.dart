import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_tts/flutter_tts.dart';
import 'package:meta_wearables/meta_wearables.dart';

void main() => runApp(const GMPInspectorApp());

class GMPInspectorApp extends StatelessWidget {
  const GMPInspectorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'GMP Inspector',
      theme: ThemeData.dark().copyWith(
        colorScheme: ColorScheme.dark(
          primary: Colors.blue.shade700,
          secondary: Colors.tealAccent,
        ),
        scaffoldBackgroundColor: const Color(0xFF0A0A0A),
      ),
      home: const InspectorHome(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class InspectorHome extends StatefulWidget {
  const InspectorHome({super.key});

  @override
  State<InspectorHome> createState() => _InspectorHomeState();
}

class _InspectorHomeState extends State<InspectorHome> {
  // Meta Wearables
  final MetaWearables _wearables = MetaWearables();
  bool _glassesConnected = false;
  Uint8List? _latestFrame;
  
  // Claude API
  static const String _apiUrl = 'https://api.anthropic.com/v1/messages';
  String _apiKey = ''; // Set via settings
  
  // Inspection state
  String _selectedSkill = 'auto';
  String _report = '';
  bool _analyzing = false;
  int _findingsCount = 0;
  double _responseTime = 0;
  
  // TTS
  final FlutterTts _tts = FlutterTts();
  bool _ttsEnabled = true;

  // System prompt (condensed for mobile)
  static const String _systemPrompt = '''You are a GMP floor inspection co-pilot for pharmaceutical environments. Analyze photos for compliance observations across 8 domains:

1. Area Status/Labeling: status tags, room classification, pressure differentials
2. Equipment: calibration stickers, ID labels, condition, storage
3. Documentation (GDP): logbooks, corrections, SOPs at point of use
4. Gowning/Personnel: proper gowning, sticky mats, no food/drink
5. Material Control: labeling, expiry, quarantine segregation, FIFO
6. Environmental: floors, walls, waste bins, lighting, vents
7. EHS Safety: eyewash, fire extinguishers, SDS, exits, PPE
8. Line Clearance: previous batch materials, labels, cleanliness

For each finding provide:
- Severity: Critical/Major/Minor/Informational/Good Practice
- Domain, Observation, Regulatory Reference, Recommended Action

Rules: Report only what you see. No fabrication. Be specific. Cite regulations. Err on reporting. Never identify the company. This is a pre-screening aid, not a GxP record.''';

  @override
  void initState() {
    super.initState();
    _initTts();
    _initWearables();
  }

  Future<void> _initTts() async {
    await _tts.setLanguage('en-US');
    await _tts.setSpeechRate(0.45);
    await _tts.setVolume(1.0);
  }

  Future<void> _initWearables() async {
    try {
      await _wearables.initialize();
      
      // Listen for connection changes
      _wearables.connectionStream.listen((connected) {
        setState(() => _glassesConnected = connected);
        if (connected) {
          _showSnack('Meta Ray-Ban connected!');
          _subscribeToCamera();
        } else {
          _showSnack('Glasses disconnected');
        }
      });
    } catch (e) {
      debugPrint('Wearables init error: $e');
    }
  }

  void _subscribeToCamera() {
    _wearables.cameraStream.listen((frame) {
      setState(() => _latestFrame = frame);
    });
  }

  Future<void> _captureAndAnalyze() async {
    if (_latestFrame == null) {
      _showSnack('No frame available. Check glasses connection.');
      return;
    }
    
    if (_apiKey.isEmpty) {
      _showApiKeyDialog();
      return;
    }

    setState(() {
      _analyzing = true;
      _report = '';
    });

    final stopwatch = Stopwatch()..start();

    try {
      final base64Image = base64Encode(_latestFrame!);
      
      final skillPrompt = {
        'auto': 'Analyze this photo from a pharmaceutical environment. Auto-detect relevant inspection domains.',
        'qa': 'Analyze for QA Floor Operations: area status, equipment, materials, documents, line clearance.',
        'ehs': 'Analyze for EHS Safety: emergency equipment, exits, chemicals, PPE, hazards.',
        'gdp': 'Analyze for Good Documentation Practice: ALCOA+, corrections, ink, logbooks.',
      }[_selectedSkill] ?? '';

      final response = await http.post(
        Uri.parse(_apiUrl),
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': _apiKey,
          'anthropic-version': '2023-06-01',
        },
        body: jsonEncode({
          'model': 'claude-sonnet-4-20250514',
          'max_tokens': 3000,
          'system': _systemPrompt,
          'messages': [{
            'role': 'user',
            'content': [
              {
                'type': 'image',
                'source': {
                  'type': 'base64',
                  'media_type': 'image/jpeg',
                  'data': base64Image,
                }
              },
              {
                'type': 'text',
                'text': skillPrompt,
              }
            ]
          }]
        }),
      );

      stopwatch.stop();

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final reportText = data['content'][0]['text'] as String;
        final findings = RegExp(r'\[\d+\]').allMatches(reportText).length;

        setState(() {
          _report = reportText;
          _findingsCount = findings;
          _responseTime = stopwatch.elapsedMilliseconds / 1000;
          _analyzing = false;
        });

        // Read critical findings aloud
        if (_ttsEnabled) {
          _speakCriticalFindings(reportText);
        }
      } else {
        setState(() {
          _report = 'API Error ${response.statusCode}: ${response.body}';
          _analyzing = false;
        });
      }
    } catch (e) {
      setState(() {
        _report = 'Error: $e';
        _analyzing = false;
      });
    }
  }

  void _speakCriticalFindings(String report) {
    final lines = report.split('\n');
    final criticals = <String>[];
    
    for (int i = 0; i < lines.length; i++) {
      if (lines[i].contains('Critical')) {
        // Get the observation line (usually 2 lines after severity)
        for (int j = i; j < i + 4 && j < lines.length; j++) {
          if (lines[j].contains('Observation:')) {
            criticals.add(lines[j].replaceFirst('Observation:', '').trim());
            break;
          }
        }
      }
    }
    
    if (criticals.isNotEmpty) {
      _tts.speak('Attention: ${criticals.length} critical findings. ${criticals.join(". ")}');
    } else {
      _tts.speak('Analysis complete. No critical findings detected.');
    }
  }

  void _showSnack(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), duration: const Duration(seconds: 2)),
    );
  }

  void _showApiKeyDialog() {
    final controller = TextEditingController(text: _apiKey);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Claude API Key'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            hintText: 'sk-ant-...',
            border: OutlineInputBorder(),
          ),
          obscureText: true,
        ),
        actions: [
          TextButton(
            onPressed: () {
              setState(() => _apiKey = controller.text.trim());
              Navigator.pop(ctx);
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('GMP Inspector'),
        centerTitle: true,
        actions: [
          // Connection indicator
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Icon(
              _glassesConnected ? Icons.bluetooth_connected : Icons.bluetooth_disabled,
              color: _glassesConnected ? Colors.greenAccent : Colors.grey,
            ),
          ),
          // Settings
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: _showApiKeyDialog,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Connection status
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: _glassesConnected 
                    ? Colors.green.withValues(alpha: 0.15)
                    : Colors.orange.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: _glassesConnected ? Colors.green : Colors.orange,
                  width: 0.5,
                ),
              ),
              child: Row(
                children: [
                  Icon(
                    _glassesConnected ? Icons.visibility : Icons.visibility_off,
                    color: _glassesConnected ? Colors.green : Colors.orange,
                  ),
                  const SizedBox(width: 12),
                  Text(
                    _glassesConnected 
                        ? 'Meta Ray-Ban Connected — Live Feed Active'
                        : 'Waiting for glasses connection...',
                    style: TextStyle(
                      color: _glassesConnected ? Colors.green : Colors.orange,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Camera preview
            if (_latestFrame != null)
              ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: Image.memory(
                  _latestFrame!,
                  fit: BoxFit.cover,
                  height: 250,
                ),
              )
            else
              Container(
                height: 250,
                decoration: BoxDecoration(
                  color: const Color(0xFF1A1A1A),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.grey.shade800),
                ),
                child: const Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.camera_alt, size: 48, color: Colors.grey),
                      SizedBox(height: 8),
                      Text('Camera feed will appear here',
                          style: TextStyle(color: Colors.grey)),
                      Text('Pair glasses via Meta View app',
                          style: TextStyle(color: Colors.grey, fontSize: 12)),
                    ],
                  ),
                ),
              ),
            const SizedBox(height: 16),

            // Skill selector
            Row(
              children: [
                _skillChip('Auto', 'auto'),
                const SizedBox(width: 8),
                _skillChip('QA', 'qa'),
                const SizedBox(width: 8),
                _skillChip('EHS', 'ehs'),
                const SizedBox(width: 8),
                _skillChip('GDP', 'gdp'),
                const Spacer(),
                // TTS toggle
                IconButton(
                  icon: Icon(
                    _ttsEnabled ? Icons.volume_up : Icons.volume_off,
                    color: _ttsEnabled ? Colors.tealAccent : Colors.grey,
                  ),
                  onPressed: () => setState(() => _ttsEnabled = !_ttsEnabled),
                  tooltip: 'Voice alerts',
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Analyze button
            ElevatedButton.icon(
              onPressed: _analyzing ? null : _captureAndAnalyze,
              icon: _analyzing 
                  ? const SizedBox(
                      width: 20, height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Icon(Icons.search, size: 24),
              label: Text(
                _analyzing ? 'Analyzing...' : 'Inspect Now',
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
                backgroundColor: Colors.blue.shade700,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
            const SizedBox(height: 16),

            // Stats
            if (_report.isNotEmpty) ...[
              Row(
                children: [
                  _statCard('Time', '${_responseTime.toStringAsFixed(1)}s'),
                  const SizedBox(width: 8),
                  _statCard('Findings', '$_findingsCount'),
                  const SizedBox(width: 8),
                  _statCard('Cost', '~\$0.02'),
                ],
              ),
              const SizedBox(height: 16),
            ],

            // Report
            if (_report.isNotEmpty)
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF111111),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.grey.shade800),
                ),
                child: SelectableText(
                  _report,
                  style: const TextStyle(
                    fontFamily: 'monospace',
                    fontSize: 13,
                    height: 1.5,
                    color: Colors.white70,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _skillChip(String label, String value) {
    final selected = _selectedSkill == value;
    return GestureDetector(
      onTap: () => setState(() => _selectedSkill = value),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: selected ? Colors.blue.shade700 : const Color(0xFF1A1A1A),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: selected ? Colors.blue : Colors.grey.shade700,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: selected ? Colors.white : Colors.grey,
            fontWeight: selected ? FontWeight.bold : FontWeight.normal,
          ),
        ),
      ),
    );
  }

  Widget _statCard(String label, String value) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: const Color(0xFF1A1A1A),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          children: [
            Text(value,
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.blue.shade300)),
            const SizedBox(height: 4),
            Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _tts.stop();
    super.dispose();
  }
}
