.class Limoblife/androidsensorbox/SplashActivity$5;
.super Ljava/lang/Object;
.source "SourceFile"

# interfaces
.implements Ljava/lang/Runnable;

# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Limoblife/androidsensorbox/SplashActivity;->onResume()V
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

    iput-object p1, p0, Limoblife/androidsensorbox/SplashActivity$5;->a:Limoblife/androidsensorbox/SplashActivity;

    iput-object p2, p0, Limoblife/androidsensorbox/SplashActivity$5;->b:Landroid/app/Dialog;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .registers 2

    iget-object v0, p0, Limoblife/androidsensorbox/SplashActivity$5;->b:Landroid/app/Dialog;

    invoke-virtual {v0}, Landroid/app/Dialog;->dismiss()V

    return-void
.end method
