package com.gusitir.lrp;

import android.app.Activity;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.net.http.SslError;
import android.os.Bundle;
import android.text.InputType;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.SslErrorHandler;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/**
 * LRP Remote: wrapper WebView para el panel de LRP OS en la red local.
 *
 * La app no tiene backend propio ni telemetria: solo abre la URL https que el
 * usuario ingresa (IP o host de la PC con LRP OS).
 */
public class MainActivity extends Activity {

    // Paleta y escala: un neutro, un acento, estados semanticos.
    private static final int COLOR_BG = 0xFFF7F8FA;
    private static final int COLOR_SURFACE = 0xFFFFFFFF;
    private static final int COLOR_BORDER = 0xFFE5E7EB;
    private static final int COLOR_TEXT = 0xFF111827;
    private static final int COLOR_MUTED = 0xFF4B5563;
    private static final int COLOR_ACCENT = 0xFF2563EB;
    private static final int COLOR_WARNING_BG = 0xFFFFF7E6;
    private static final int COLOR_WARNING_BORDER = 0xFFF59E0B;
    private static final int COLOR_WARNING_TEXT = 0xFF92400E;
    private static final int COLOR_ERROR = 0xFFB91C1C;

    private static final String PREFS = "lrp_remote";
    private static final String KEY_LAST_URL = "last_url";
    private static final String DEFAULT_HOST = "lrp.local";
    private static final String WARNING_TEXT =
            "Esta app acepta el certificado del equipo sin validarlo. Usala solo en tu red local.";

    private SharedPreferences prefs;
    private ScrollView setupScroll;
    private LinearLayout webContainer;
    private TextView webErrorBar;
    private EditText urlInput;
    private TextView setupError;
    private WebView webView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = getSharedPreferences(PREFS, MODE_PRIVATE);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(COLOR_BG);

        setupScroll = new ScrollView(this);
        setupScroll.setFillViewport(true);
        setupScroll.addView(buildSetupPanel(), new ScrollView.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        webContainer = new LinearLayout(this);
        webContainer.setOrientation(LinearLayout.VERTICAL);
        webContainer.setBackgroundColor(COLOR_SURFACE);
        webContainer.setVisibility(View.GONE);

        webErrorBar = new TextView(this);
        webErrorBar.setTextSize(14f);
        webErrorBar.setTextColor(Color.WHITE);
        webErrorBar.setBackgroundColor(COLOR_ERROR);
        webErrorBar.setPadding(dp(16), dp(12), dp(16), dp(12));
        webErrorBar.setVisibility(View.GONE);
        webContainer.addView(webErrorBar, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        root.addView(setupScroll, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));
        root.addView(webContainer, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        setContentView(root);
    }

    private View buildSetupPanel() {
        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);
        form.setPadding(dp(24), dp(32), dp(24), dp(24));

        TextView title = new TextView(this);
        title.setText("LRP Remote");
        title.setTextSize(24f);
        title.setTypeface(Typeface.create("sans-serif", Typeface.BOLD));
        title.setTextColor(COLOR_TEXT);
        form.addView(title);

        TextView subtitle = new TextView(this);
        subtitle.setText("Controlá tu TV por la red local.");
        subtitle.setTextSize(16f);
        subtitle.setTextColor(COLOR_MUTED);
        subtitle.setPadding(0, dp(8), 0, 0);
        form.addView(subtitle);

        TextView warning = new TextView(this);
        warning.setText(WARNING_TEXT);
        warning.setTextSize(16f);
        warning.setTextColor(COLOR_WARNING_TEXT);
        warning.setBackground(rounded(COLOR_WARNING_BG, COLOR_WARNING_BORDER, 12));
        warning.setPadding(dp(16), dp(16), dp(16), dp(16));
        LinearLayout.LayoutParams warningLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        warningLp.topMargin = dp(24);
        form.addView(warning, warningLp);

        TextView label = new TextView(this);
        label.setText("IP o host de la PC");
        label.setTextSize(14f);
        label.setTypeface(Typeface.create("sans-serif", Typeface.BOLD));
        label.setTextColor(COLOR_MUTED);
        LinearLayout.LayoutParams labelLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        labelLp.topMargin = dp(24);
        form.addView(label, labelLp);

        urlInput = new EditText(this);
        urlInput.setSingleLine(true);
        urlInput.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        urlInput.setTextSize(16f);
        urlInput.setTextColor(COLOR_TEXT);
        urlInput.setHint("192.168.1.20 o " + DEFAULT_HOST);
        urlInput.setHintTextColor(COLOR_MUTED);
        urlInput.setBackground(rounded(COLOR_SURFACE, COLOR_BORDER, 12));
        urlInput.setPadding(dp(16), dp(14), dp(16), dp(14));
        String lastUrl = prefs.getString(KEY_LAST_URL, "");
        urlInput.setText(lastUrl.isEmpty() ? DEFAULT_HOST : lastUrl);
        LinearLayout.LayoutParams inputLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        inputLp.topMargin = dp(8);
        form.addView(urlInput, inputLp);

        setupError = new TextView(this);
        setupError.setTextSize(14f);
        setupError.setTextColor(COLOR_ERROR);
        setupError.setVisibility(View.GONE);
        LinearLayout.LayoutParams errorLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        errorLp.topMargin = dp(8);
        form.addView(setupError, errorLp);

        Button connect = new Button(this);
        connect.setText("Conectar");
        connect.setAllCaps(false);
        connect.setTextSize(16f);
        connect.setTextColor(Color.WHITE);
        connect.setBackground(rounded(COLOR_ACCENT, Color.TRANSPARENT, 12));
        LinearLayout.LayoutParams buttonLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(48));
        buttonLp.topMargin = dp(16);
        form.addView(connect, buttonLp);
        connect.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                connect();
            }
        });

        TextView caption = new TextView(this);
        caption.setText("La URL se guarda solo en este dispositivo. La app no envía datos a terceros.");
        caption.setTextSize(14f);
        caption.setTextColor(COLOR_MUTED);
        LinearLayout.LayoutParams captionLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        captionLp.topMargin = dp(24);
        form.addView(caption, captionLp);

        return form;
    }

    private void connect() {
        String normalized = normalizeUrl(urlInput.getText().toString());
        if (normalized == null) {
            showSetupError("Ingresá una IP o un host válido, por ejemplo 192.168.1.20.");
            return;
        }
        urlInput.setText(normalized);
        prefs.edit().putString(KEY_LAST_URL, normalized).apply();
        setupError.setVisibility(View.GONE);
        showWeb(normalized);
    }

    /**
     * Acepta "192.168.1.20", "lrp.local", "lrp.local:8000" o una URL completa.
     * Fuerza https y agrega :8000 cuando falta el puerto.
     */
    private String normalizeUrl(String raw) {
        if (raw == null) {
            return null;
        }
        String value = raw.trim();
        value = value.replaceFirst("(?i)^https?://", "");
        if (value.isEmpty()) {
            return null;
        }
        Uri uri;
        try {
            uri = Uri.parse("https://" + value);
        } catch (Exception e) {
            return null;
        }
        String host = uri.getHost();
        if (host == null || host.isEmpty()) {
            return null;
        }
        if (uri.getPort() == -1) {
            uri = uri.buildUpon().authority(host + ":8000").build();
        }
        return uri.toString();
    }

    private void showWeb(String url) {
        setupScroll.setVisibility(View.GONE);
        webContainer.setVisibility(View.VISIBLE);
        webErrorBar.setVisibility(View.GONE);
        if (webView == null) {
            webView = buildWebView();
            LinearLayout.LayoutParams webLp = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f);
            webContainer.addView(webView, webLp);
        }
        webView.loadUrl(url);
    }

    private WebView buildWebView() {
        WebView view = new WebView(this);
        WebSettings settings = view.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);

        view.setWebChromeClient(new WebChromeClient());
        view.setWebViewClient(new WebViewClient() {
            @Override
            public void onReceivedSslError(WebView web, SslErrorHandler handler, SslError error) {
                // LRP OS es LAN-only y usa una CA local que el telefono no conoce.
                // Aceptar el certificado es una decision explicita del dueno: la UI
                // avisa que no se valida y que solo se use en la red local.
                handler.proceed();
            }

            @Override
            public void onReceivedError(WebView web, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) {
                    showWebError(error.getDescription() != null
                            ? error.getDescription().toString()
                            : "sin detalle");
                }
            }

            @Override
            public void onPageStarted(WebView web, String url, android.graphics.Bitmap favicon) {
                webErrorBar.setVisibility(View.GONE);
            }
        });
        return view;
    }

    private void showSetupError(String message) {
        setupError.setText(message);
        setupError.setVisibility(View.VISIBLE);
    }

    private void showWebError(String detail) {
        webErrorBar.setText("No se pudo conectar: " + detail
                + "\nRevisá la IP, el puerto 8000 y que el panel esté encendido.");
        webErrorBar.setVisibility(View.VISIBLE);
    }

    private void returnToSetup() {
        if (webView != null) {
            webContainer.removeView(webView);
            webView.destroy();
            webView = null;
        }
        webContainer.setVisibility(View.GONE);
        setupScroll.setVisibility(View.VISIBLE);
        webErrorBar.setVisibility(View.GONE);
    }

    @Override
    public void onBackPressed() {
        if (webContainer.getVisibility() == View.VISIBLE) {
            if (webView != null && webView.canGoBack()) {
                webView.goBack();
                return;
            }
            returnToSetup();
            return;
        }
        super.onBackPressed();
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.destroy();
            webView = null;
        }
        super.onDestroy();
    }

    private GradientDrawable rounded(int fill, int stroke, int radiusDp) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(fill);
        drawable.setCornerRadius(dp(radiusDp));
        if (stroke != Color.TRANSPARENT) {
            drawable.setStroke(dp(1), stroke);
        }
        return drawable;
    }

    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }
}
