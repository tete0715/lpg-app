import 'dart:math';
import 'package:flutter/material.dart';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'package:intl/intl.dart';

void main() => runApp(const MaterialApp(home: LPGApp(), debugShowCheckedModeBanner: false));

class LPGApp extends StatefulWidget {
  const LPGApp({super.key});
  @override
  State<LPGApp> createState() => _LPGAppState();
}

class _LPGAppState extends State<LPGApp> {
  Database? db;
  final cidCtrl = TextEditingController(), nameCtrl = TextEditingController(), phoneCtrl = TextEditingController();
  Map<String, dynamic>? user;
  List<Map<String, dynamic>> history = [];
  int daysLeft = 0;

  @override
  void initState() {
    super.initState();
    _initDB();
  }

  void _initDB() async {
    db = await openDatabase(join(await getDatabasesPath(), 'lpg.db'), version: 1, onCreate: (d, v) {
      d.execute('CREATE TABLE clients (cid TEXT PRIMARY KEY, name TEXT, phone TEXT)');
      d.execute('CREATE TABLE bookings (cid TEXT, date TEXT)');
    });
  }

  void _register() async {
    try {
      await db?.insert('clients', {'cid': cidCtrl.text, 'name': nameCtrl.text, 'phone': phoneCtrl.text});
      _snack('🎉 Registered successfully!');
    } catch (_) {
      _snack('❌ Consumer ID already exists!');
    }
  }

  void _login() async {
    var u = await db?.query('clients', where: 'cid = ?', whereArgs: [cidCtrl.text]);
    if (u != null && u.isNotEmpty) {
      var h = await db?.query('bookings', where: 'cid = ?', whereArgs: [cidCtrl.text]);
      setState(() {
        user = u.first;
        history = h ?? [];
        if (history.isNotEmpty) {
          DateTime last = DateFormat('dd-MM-yyyy').parse(history.last['date']);
          daysLeft = 30 - DateTime.now().difference(last).inDays;
        } else {
          daysLeft = 0;
        }
      });
    } else {
      _snack('❌ Account not found.');
    }
  }

  void _book() {
    String otp = (1000 + Random().nextInt(9000)).toString();
    final otpCtrl = TextEditingController();
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: Text('OTP sent to ${user!['phone']}: $otp'),
        content: TextField(controller: otpCtrl, decoration: const InputDecoration(labelText: 'Enter OTP')),
        actions: [
          TextButton(
            onPressed: () async {
              if (otpCtrl.text == otp) {
                String today = DateFormat('dd-MM-yyyy').format(DateTime.now());
                await db?.insert('bookings', {'cid': user!['cid'], 'date': today});
                Navigator.pop(context);
                _login();
                _snack('🎉 Booked for $today!');
              } else {
                _snack('❌ Invalid OTP!');
              }
            },
            child: const Text('Confirm'),
          )
        ],
      ),
    );
  }

  void _snack(String msg) => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('LPG Booking'), backgroundColor: Colors.deepOrange),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: ListView(
          children: [
            TextField(controller: cidCtrl, decoration: const InputDecoration(labelText: 'Consumer ID')),
            TextField(controller: nameCtrl, decoration: const InputDecoration(labelText: 'Name')),
            TextField(controller: phoneCtrl, decoration: const InputDecoration(labelText: 'Phone')),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(child: ElevatedButton(onPressed: _register, child: const Text('Register'))),
                const SizedBox(width: 10),
                Expanded(child: ElevatedButton(onPressed: _login, child: const Text('Login'))),
              ],
            ),
            if (user != null) ...[
              const Divider(height: 30),
              Text('👤 ${user!['name']} (${user!['cid']})', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 10),
              Text('History: ${history.map((e) => e['date']).join(', ')}'),
              const SizedBox(height: 10),
              Text(
                daysLeft > 0 ? '⏳ Next booking in $daysLeft days' : '✅ Ready to book today!',
                style: TextStyle(color: daysLeft > 0 ? Colors.red : Colors.green, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 10),
              ElevatedButton(onPressed: daysLeft <= 0 ? _book : null, child: const Text('Book Now')),
            ]
          ],
        ),
      ),
    );
  }
}
