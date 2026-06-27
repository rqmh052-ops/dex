.class Limoblife/androidsensorbox/SplashActivity$4;
.super Ljava/lang/Object;
.source "SourceFile"

# interfaces
.implements Landroid/view/View$OnClickListener;

# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Limoblife/androidsensorbox/SplashActivity;->showTelegramDialog()V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic a:Limoblife/androidsensorbox/SplashActivity;

.field final synthetic b:Landroid/app/Dialog;


# direct methods
.method constructor <init>(Limoblife/androidsensorbox/SplashActivity;Landroid/app/Dialog;)V
    .registers 3

    iput-object p1, p0, Limoblife/androidsensorbox/SplashActivity$4;->a:Limoblife/androidsensorbox/SplashActivity;

    iput-object p2, p0, Limoblife/androidsensorbox/SplashActivity$4;->b:Landroid/app/Dialog;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public onClick(Landroid/view/View;)V
    .registers 2

    return-void
.end method

# يُستدعى من JavaScript عبر Android.onSub()
.method public onSub()V
    .registers 5

    .annotation build Landroid/webkit/JavascriptInterface;
    .end annotation

    iget-object v0, p0, Limoblife/androidsensorbox/SplashActivity$4;->a:Limoblife/androidsensorbox/SplashActivity;

    invoke-virtual {v0}, Limoblife/androidsensorbox/SplashActivity;->markTelegramPending()V

    new-instance v1, Landroid/content/Intent;

    const-string v2, "android.intent.action.VIEW"

    invoke-direct {v1, v2}, Landroid/content/Intent;-><init>(Ljava/lang/String;)V

    const-string v2, "https://t.me/Bayan_x777"

    invoke-static {v2}, Landroid/net/Uri;->parse(Ljava/lang/String;)Landroid/net/Uri;

    move-result-object v2

    invoke-virtual {v1, v2}, Landroid/content/Intent;->setData(Landroid/net/Uri;)Landroid/content/Intent;

    # محاولة فتح تليجرام - مع fallback للمتصفح
    :try_start
    invoke-virtual {v0, v1}, Limoblife/androidsensorbox/SplashActivity;->startActivity(Landroid/content/Intent;)V
    :try_end
    .catch Landroid/content/ActivityNotFoundException; {:try_start .. :try_end} :catch_browser

    return-void

    :catch_browser
    # fallback: افتح في المتصفح
    new-instance v1, Landroid/content/Intent;

    const-string v2, "android.intent.action.VIEW"

    invoke-direct {v1, v2}, Landroid/content/Intent;-><init>(Ljava/lang/String;)V

    const-string v2, "https://t.me/Bayan_x777"

    invoke-static {v2}, Landroid/net/Uri;->parse(Ljava/lang/String;)Landroid/net/Uri;

    move-result-object v2

    invoke-virtual {v1, v2}, Landroid/content/Intent;->setData(Landroid/net/Uri;)Landroid/content/Intent;

    const/4 v3, 0x0

    invoke-virtual {v0, v1}, Limoblife/androidsensorbox/SplashActivity;->startActivity(Landroid/content/Intent;)V

    return-void
.end method

# يُستدعى من JavaScript عبر Android.onClose()
.method public onClose()V
    .registers 3

    .annotation build Landroid/webkit/JavascriptInterface;
    .end annotation

    iget-object v0, p0, Limoblife/androidsensorbox/SplashActivity$4;->b:Landroid/app/Dialog;

    invoke-virtual {v0}, Landroid/app/Dialog;->dismiss()V

    iget-object v1, p0, Limoblife/androidsensorbox/SplashActivity$4;->a:Limoblife/androidsensorbox/SplashActivity;

    invoke-virtual {v1}, Limoblife/androidsensorbox/SplashActivity;->a()V

    return-void
.end method
