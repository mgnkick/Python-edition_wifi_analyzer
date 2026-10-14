package com.azaza.networktool;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.net.wifi.ScanResult;
import android.net.wifi.WifiManager;
import android.os.Build;
import android.os.Bundle;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class MainActivity extends AppCompatActivity {

    private WebView webView;
    private static final int PERMISSION_REQ_CODE = 1001;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        webView = new WebView(this);
        setContentView(webView);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);

        webView.setWebViewClient(new WebViewClient());
        webView.addJavascriptInterface(new AndroidBridge(), "AndroidBridge");

        checkAndRequestPermissions();

        // Load offline embedded assets
        webView.loadUrl("file:///android_asset/index.html");
    }

    private void checkAndRequestPermissions() {
        List<String> perms = new ArrayList<>();
        perms.add(Manifest.permission.ACCESS_FINE_LOCATION);
        perms.add(Manifest.permission.ACCESS_COARSE_LOCATION);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            perms.add(Manifest.permission.NEARBY_WIFI_DEVICES);
        }

        List<String> needed = new ArrayList<>();
        for (String p : perms) {
            if (ContextCompat.checkSelfPermission(this, p) != PackageManager.PERMISSION_GRANTED) {
                needed.add(p);
            }
        }

        if (!needed.isEmpty()) {
            ActivityCompat.requestPermissions(this, needed.toArray(new String[0]), PERMISSION_REQ_CODE);
        }
    }

    public class AndroidBridge {

        @JavascriptInterface
        public boolean isAndroid() {
            return true;
        }

        @JavascriptInterface
        public String getNetworkStatus() {
            try {
                ConnectivityManager cm = (ConnectivityManager) getSystemService(Context.CONNECTIVITY_SERVICE);
                boolean hasWifi = false;
                boolean hasMobile = false;
                boolean hasVpn = false;

                if (cm != null) {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                        Network activeNet = cm.getActiveNetwork();
                        if (activeNet != null) {
                            NetworkCapabilities caps = cm.getNetworkCapabilities(activeNet);
                            if (caps != null) {
                                hasWifi = caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI);
                                hasMobile = caps.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR);
                                hasVpn = caps.hasTransport(NetworkCapabilities.TRANSPORT_VPN);
                            }
                        }
                    }
                }

                JSONObject res = new JSONObject();
                List<String> warnings = new ArrayList<>();

                if (!hasWifi) {
                    warnings.add("Внимание: Wi-Fi интерфейс отключен или отсутствует в системе.");
                }
                if (hasMobile) {
                    warnings.add("Обнаружено использование мобильного интернета (сотовая связь).");
                }
                if (hasVpn) {
                    warnings.add("Обнаружено активное VPN-соединение (туннельный интерфейс).");
                }

                String connType = "Ethernet / Локальная";
                if (hasWifi) connType = "Wi-Fi Активен";
                if (hasMobile) connType = "Мобильный интернет";
                if (hasVpn) connType += " + VPN";

                res.put("local_ip", "127.0.0.1");
                res.put("gateway", "192.168.1.1");
                res.put("connection_type", connType);
                res.put("warnings", new JSONArray(warnings));

                return res.toString();
            } catch (Exception e) {
                return "{\"error\":\"" + e.getMessage() + "\"}";
            }
        }

        @JavascriptInterface
        public String getWifiNetworks() {
            try {
                WifiManager wm = (WifiManager) getApplicationContext().getSystemService(Context.WIFI_SERVICE);
                if (wm == null || !wm.isWifiEnabled()) {
                    return "{\"error\":\"Модуль Wi-Fi отключен на устройстве. Включите Wi-Fi в настройках Android.\"}";
                }

                if (ActivityCompat.checkSelfPermission(MainActivity.this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
                    return "{\"error\":\"Необходимо предоставить разрешение на доступ к геолокации для сканирования Wi-Fi на Android.\"}";
                }

                List<ScanResult> results = wm.getScanResults();
                if (results == null || results.isEmpty()) {
                    return "{\"networks\":[]}";
                }

                // Group by SSID
                Map<String, JSONObject> ssidMap = new HashMap<>();

                for (ScanResult sr : results) {
                    String ssid = sr.SSID != null && !sr.SSID.isEmpty() ? sr.SSID : "<Скрытая сеть>";
                    int channel = (sr.frequency - 2407) / 5;
                    String freqStr = sr.frequency + " МГц";

                    JSONObject netObj = ssidMap.get(ssid);
                    if (netObj == null) {
                        netObj = new JSONObject();
                        netObj.put("ssid", ssid);
                        netObj.put("security", sr.capabilities);
                        netObj.put("bssids", new JSONArray());
                        ssidMap.put(ssid, netObj);
                    }

                    JSONObject bssidObj = new JSONObject();
                    bssidObj.put("bssid", sr.BSSID);
                    bssidObj.put("channel", String.valueOf(channel));
                    bssidObj.put("freq", freqStr);
                    bssidObj.put("rssi", sr.level);
                    bssidObj.put("vendor", "Android Драйвер");

                    netObj.getJSONArray("bssids").put(bssidObj);
                }

                JSONArray netArray = new JSONArray();
                for (JSONObject o : ssidMap.values()) {
                    netArray.put(o);
                }

                JSONObject out = new JSONObject();
                out.put("networks", netArray);
                return out.toString();

            } catch (Exception e) {
                return "{\"error\":\"Ошибка сканирования Android: " + e.getMessage() + "\"}";
            }
        }

        @JavascriptInterface
        public String getArpTable() {
            try {
                JSONArray devices = new JSONArray();
                BufferedReader br = new BufferedReader(new FileReader("/proc/net/arp"));
                String line;
                boolean first = true;
                while ((line = br.readLine()) != null) {
                    if (first) {
                        first = false;
                        continue;
                    }
                    String[] parts = line.trim().split("\\s+");
                    if (parts.length >= 6 && !parts[3].equals("00:00:00:00:00:00")) {
                        JSONObject dev = new JSONObject();
                        dev.put("ip", parts[0]);
                        dev.put("mac", parts[3]);
                        dev.put("iface", parts[5]);
                        dev.put("hostname", "сосед");
                        devices.put(dev);
                    }
                }
                br.close();

                JSONObject out = new JSONObject();
                out.put("devices", devices);
                return out.toString();
            } catch (Exception e) {
                return "{\"devices\":[]}";
            }
        }

        @JavascriptInterface
        public String pingHost(String host, String count, String size) {
            try {
                int c = Integer.parseInt(count);
                int s = Integer.parseInt(size);
                Process proc = Runtime.getRuntime().exec(new String[]{"ping", "-c", String.valueOf(c), "-s", String.valueOf(s), host});
                BufferedReader reader = new BufferedReader(new InputStreamReader(proc.getInputStream()));
                List<String> logs = new ArrayList<>();
                logs.add("ICMP ПИНГ: узел=" + host + ", размер=" + size + " байт, попыток=" + count + ":");
                String line;
                while ((line = reader.readLine()) != null) {
                    if (!line.trim().isEmpty()) {
                        logs.add(line);
                    }
                }
                proc.waitFor();
                reader.close();

                JSONObject out = new JSONObject();
                out.put("logs", new JSONArray(logs));
                return out.toString();
            } catch (Exception e) {
                return "{\"logs\":[\"Ошибка ICMP пинга Android: " + e.getMessage() + "\"]}";
            }
        }
    }
}
