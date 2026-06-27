.class Limoblife/androidsensorbox/SplashActivity$6;
.super Landroid/webkit/WebViewClient;
.source "SourceFile"

.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Limoblife/androidsensorbox/SplashActivity;->showTelegramDialog()V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation

.field final synthetic a:Limoblife/androidsensorbox/SplashActivity;

.method constructor <init>(Limoblife/androidsensorbox/SplashActivity;)V
    .registers 2

    iput-object p1, p0, Limoblife/androidsensorbox/SplashActivity$6;->a:Limoblife/androidsensorbox/SplashActivity;

    invoke-direct {p0}, Landroid/webkit/WebViewClient;-><init>()V

    return-void
.end method

# API قديمة (Android < 24) — مطلوبة للتوافق
.method public shouldOverrideUrlLoading(Landroid/webkit/WebView;Ljava/lang/String;)Z
    .registers 6

    const-string v0, "https://t.me/"

    invoke-virtual {p2, v0}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :skip

    iget-object v0, p0, Limoblife/androidsensorbox/SplashActivity$6;->a:Limoblife/androidsensorbox/SplashActivity;

    invoke-virtual {v0}, Limoblife/androidsensorbox/SplashActivity;->markTelegramPending()V

    new-instance v1, Landroid/content/Intent;

    const-string v2, "android.intent.action.VIEW"

    invoke-direct {v1, v2}, Landroid/content/Intent;-><init>(Ljava/lang/String;)V

    invoke-static {p2}, Landroid/net/Uri;->parse(Ljava/lang/String;)Landroid/net/Uri;

    move-result-object v2

    invoke-virtual {v1, v2}, Landroid/content/Intent;->setData(Landroid/net/Uri;)Landroid/content/Intent;

    :try_start
    invoke-virtual {v0, v1}, Limoblife/androidsensorbox/SplashActivity;->startActivity(Landroid/content/Intent;)V
    :try_end
    .catch Landroid/content/ActivityNotFoundException; {:try_start .. :try_end} :catch_skip

    const/4 v0, 0x1

    return v0

    :catch_skip
    const/4 v0, 0x0

    return v0

    :skip
    const/4 v0, 0x0

    return v0
.end method
