---
theme: cyanosis
---

macOS 搞定了，接下来是 Windows。作为全球桌面端占有率最高的操作系统，Windows 版本是 IM 应用不可或缺的一环。本章之后，四大主流平台就齐活了。本章围绕以下几个点展开：

- 如何构建 Windows 桌面应用产物
- MSIX 打包与 Microsoft Store 分发
- exe 安装包打包（Inno Setup）
- 桌面端登录页优化：扫码登录 + 左右分栏布局

> Flutter 的 Windows 支持已经 stable，同一套代码无需修改即可编译为 Windows 应用。

Windows 桌面端构建与扫码登录，在 `v0.27.0` 迭代里，模块是 `auth/v0.0.5`

| 模块名 | 功能分析 | 后端设计 | 后端任务 | 前端设计 | 前端任务 |
| --- | --- | --- | --- | --- | --- |
| auth/v0.0.5 | [analysis.md](https://github.com/toly1994328/flash_im_by_ai/tree/master/docs/features/auth/v0.0.5/analysis.md) | [design.md](https://github.com/toly1994328/flash_im_by_ai/tree/master/docs/features/auth/v0.0.5/server/design.md) | [tasks.md](https://github.com/toly1994328/flash_im_by_ai/tree/master/docs/features/auth/v0.0.5/server/tasks.md) | [design.md](https://github.com/toly1994328/flash_im_by_ai/tree/master/docs/features/auth/v0.0.5/client/design.md) | [tasks.md](https://github.com/toly1994328/flash_im_by_ai/tree/master/docs/features/auth/v0.0.5/client/tasks.md) |


---

#### 一、构建 Windows 前置准备

Windows 构建比 macOS 简单得多——不需要签名证书、不需要公证、不需要 Xcode。只要有 Visual Studio 和 Flutter SDK，一条命令就能出产物。同样 windows 也有对应的工作目录，和 windows原生相关的，都需要在这里处理：

![image.png](https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/b3d891a9ba1d4bf9b2de6cf2cf9936a5~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1125&h=645&s=44928&e=png&b=f6f7f9)

---

##### 1. 前置环境

Windows 构建需要：
- Flutter SDK（stable channel）
- Visual Studio 2022（含"使用 C++ 的桌面开发"工作负载）
- Windows 10 SDK

确认环境就绪：

```bash
flutter doctor
```

看到 `[✓] Visual Studio - develop Windows apps` 就行。

---

##### 2. 应用图标

**相关文件位置**（`client/windows/runner/resources/app_icon.ico`）：

Windows 用 `.ico` 格式，项目里已经准备了生成脚本，一条命令搞定：

```bash
python scripts/build_center/res/gen_ico.py
```

默认从 `client/assets/images/logo.png` 生成，输出到 `client/windows/runner/resources/app_icon.ico`。也可以指定源图：

```bash
python scripts/build_center/res/gen_ico.py
```

> 前置：`pip install Pillow`

替换后重新构建，exe 文件图标和任务栏图标都会更新。


![image.png](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/2d75c93272814adf8a6e7f5622689183~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1158&h=331&s=139787&e=png&b=e2ecf9)

---

##### 3. 运行项目

开发阶段直接运行下面的命令，就可以启动测试环境下的，闪讯 Windows 桌面端了

```bash
cd client
flutter run -d windows --dart-define-from-file=.env.dev
```

支持热重载，体验和移动端一致。我们上一章支持的 MacOS 桌面端，消息页 UI 适配，在 windows 下依然生效。

---

#### 二、 Windows 应用打包与分发 exe

能本地跑起来是第一步，如何打包分发给其他人用，才是产品的最终归宿。windows 用户非常熟悉的是 `.exe` 的安装包，双击就可以逐步安装应用。为了展示整个流程，我还是会一步步拆解流程，让大家对产物有个基本认知。最终还是会通过脚本 `一站式构建` 产物。

---

##### 1. 产物是什么

首先，可以用 flutter 本身的命令来构建产物:

```bash
cd client
flutter build windows --release --dart-define-from-file=.env.production
```

产物在 `client/build/windows/x64/runner/Release` 文件夹内，在这里双击 `flash_im` 就可以启动。其实此时你把整个 Release 压缩发给别人，对方就可以在 windows 上运行了。


![image.png](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/9d55ee25093a403bac1937d944571488~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=887&h=338&s=39526&e=png&b=ffffff)

但这样并不利于分发，毕竟对方还要解压，也没有安装的流程。传统的 `.exe` 安装程序是 Windows 用户最熟悉的方式，下面将介绍一下如何打包成整个的 `.exe` 安装包。

---

##### 2. 安装 Inno Setup


Inno Setup 是一个免费的安装包制作工具，配置简单，产出的安装程序体积小、兼容性好。从 [jrsoftware.org](https://jrsoftware.org/isdl.php) 下载安装 Inno Setup 6。下载安装上就不用管了，以后我们通过 `脚本`来操作，不过要记得你安装到了哪个目录下。比如我安装在： 

> C:\Program Files (x86)\Inno Setup 6

![image.png](https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/f1a4e95216294061b4ee3b4f36bc0071~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=984&h=136&s=22185&e=png&b=dfe9f2)

---


##### 3. 打包脚本

本质上 Inno Setup 是在 flutter 构建完成后的基础上进行的二次加工。我们对所有平台产物的构建，最终都会基于 `python` 脚本来完成，统一维护在 `scripts/build_center` 下。有些平台打包时可能有多个需要使用的脚本，比如这里的 windows 通过独立文件夹维护，职责更加清楚。能通过一个脚本完成的暂时就放在外面：


![image.png](https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/8a0b26509d8f4c2fa2f938250033425a~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1005&h=429&s=36819&e=png&b=f1f0f3)

`scripts\build_center\build.json` 里放置一些需要的外界依赖。比如 `Inno Setup 6` 的安装位置。这样 python 脚本才能访问到它，基于 `flash_im.iss` 构建产出: 

```
{
  "windows": {
    "inno_setup": "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"
  }
}
```

执行脚本后，可以看到产物在 `build_center/dest/windows` 下

> python scripts/build_center/windows/build.py --pack

![image.png](https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/05de4a5daa484fb68302a8e5fa6f4968~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=814&h=326&s=21703&e=png&b=f2f1f4)

双击安装包，就可以打开安装界面。这个 `flash_im.exe` 就可以作为最终分发的产物了。

![image.png](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/b2757664b153424d9ec65f83d666d993~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=986&h=311&s=25012&e=png&b=fdfdfd)

这里关于 [flash_im.iss]() 的脚本内容，就不介绍了，感兴趣的可以让 AI 为你讲解一下。这里可以留个小作业：  
默认 Inno Setup 打包的 exe , 安装界面不支持中文，大家可以在 AI 的帮助下下，看看如何支持一下。

---


#### 三、打包 MSIX 

如果想上架 Microsoft Store，用 MSIX 格式打包。MSIX 是微软推荐的现代打包格式，类似 macOS 的 .app。


##### 1. 添加 msix 依赖

`msix` 插件可以非常方便地打包 `.msix` 产物。在 `client/pubspec.yaml` 的 `dev_dependencies` 中添加：

```yaml
dev_dependencies:
  msix: ^3.16.0
```

---

##### 2. 配置 msix

在 `client/pubspec.yaml` 末尾添加：

```yaml
msix_config:
  display_name: 闪讯
  publisher_display_name: toly
  identity_name: com.toly1994.flashIm
  msix_version: 1.0.0+2
  logo_path: assets/images/logo.png
```

---

##### 3. 打包 msix 产物

产物在 `Release` 的同级目录：

```bash
flutter pub run msix:create
```

![image.png](https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/3c574dea886a4c8ebce57762c726eb88~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=810&h=374&s=45496&e=png&b=ffffff)

但是这样打的包，别人安装不了，因为无法验证包的发布者。

![image.png](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/f6117c7bc84c4fb08a2800eab8e59d28~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=975&h=586&s=63031&e=png&b=f2f2f2)

打包时 msix 包会自动生成一个测试证书用于签名。这个证书只有你自己的电脑信任，别人的电脑不认。

- **本机测试**：第一次打包时选择安装证书（输入 y），之后本机可以直接安装 msix
- **发给别人**：对方需要先安装你的证书才能装 msix，比较麻烦
- **上架 Store**：微软会用自己的证书重新签名，用户从 Store 安装完全不需要管证书


上架需要在 [Microsoft Partner Center](https://partner.microsoft.com/) 注册开发者账号，获取应用的 `publisher`、`identity_name` 等值填入 `msix_config`。上传 msix 后微软审核通过即可上架。但是 Microsoft 商店国内用户很难访问，不如直接使用 `.exe` 挂在网站上分发。


---

#### 四、桌面端登录页优化

这一版除了构建流程，还做了一个重要的功能迭代：**桌面端扫码登录 + 登录页左右分栏布局**。移动端的登录页直接跑在桌面端上很别扭，是一个窄窄的表单撑满整个大屏幕，GitHub 和 Apple 登录按钮在 Windows 上也没有意义。需要针对大屏幕重新设计交互进行。


| 邮箱登录 | 密码登录 |
| --- | --- |
| 
![image.png](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/ea8eee9617044ab6b3090bd7c03f4af1~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1059&h=741&s=159490&e=png&b=e4effc) | ![image.png](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/c1e4f4c4d02a4096a70d71a91d5e377d~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1059&h=741&s=157241&e=png&b=e4effc) |




---

##### 1. 扫码登录流程

桌面端不想支持三方登录（GitHub 需要浏览器回调，Apple 只支持 iOS/macOS），但用户又不想每次输密码。解决方案：**手机扫码登录**。

| 展示二维码 | 二维码超时支持刷新 |
| --- | --- |
|  ![image.png](https://p6-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/7476f90e84954ed0888cc5a405e55fe4~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1059&h=741&s=147481&e=png&b=e7f1fc) | ![image.png](https://p6-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/295ed1ef2cf444fd9851e83d9ee722df~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1059&h=741&s=150369&e=png&b=e7f1fc) |


流程大致如下: 

1. 桌面端显示二维码（内容是 `flashim://scan/{token}`）
2. 手机端打开闪讯扫一扫，识别到 scan 协议
3. 手机端跳转确认页，点击"确认登录"
4. 桌面端自动登录进入主页


![mermaid-diagram - 2026-05-30T082200.650.png](https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/aa5cc724a4364fc2a9621c03a214e6a3~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1847&h=1998&s=203519&e=png&a=1&b=e9e9e9)





---

##### 2. 后端实现

后端新增了一张 `scan_sessions` 表，字段不多：

| 字段 | 类型 | 说明 |
|------|------|------|
| token | VARCHAR(36) | UUID 主键，就是二维码里的那个 token |
| status | SMALLINT | 0=等待扫码 1=已扫码 2=已确认 3=已取消 |
| user_id | BIGINT | 谁扫的（扫码后填入） |
| expires_at | TIMESTAMPTZ | 5 分钟后过期 |

围绕这张表，后端提供了 4 个接口，各司其职：

- **scan_create**：桌面端调用。生成一个 UUID 写入表，返回 `flashim://scan/{token}` 给前端渲染二维码。
- **scan_status**：桌面端每 2 秒调一次。查表看 status 变了没，变了就告诉前端。confirmed 时额外返回 JWT。
- **scan_confirm**：手机端调用，分两步。第一步 `action=scan` 把 status 从 0 改成 1，同时记下 user_id；第二步 `action=confirm` 把 status 从 1 改成 2。
- **scan_cancel**：手机端取消，把 status 改成 3。

整个设计的核心思路：**桌面端和手机端不直接通信**，而是各自和后端交互，通过数据库里的一行记录传递状态。状态流转：`pending → scanned → confirmed`。桌面端轮询到 confirmed 时，响应里带着 JWT token，直接登录。  

```rust
---->[flash-auth/src/handler.rs]----
/// POST /auth/scan/create — 创建扫码会话
pub async fn scan_create(State(state): State<Arc<AppState>>) -> Result<...> {
    let token = uuid::Uuid::new_v4().to_string();
    let expires_at = Utc::now() + chrono::Duration::minutes(5);
    // INSERT INTO scan_sessions (token, status, expires_at)
    let qr_content = format!("flashim://scan/{}", token);
    Ok(Json(ScanCreateResponse { token, qr_content, expires_at }))
}

/// GET /auth/scan/status — 桌面端轮询
pub async fn scan_status(...) -> Result<...> {
    // SELECT status, user_id, expires_at FROM scan_sessions WHERE token = $1
    // 根据 status 返回：pending / scanned / confirmed（带 JWT）/ expired
}

/// POST /auth/scan/confirm — 手机端扫码/确认
pub async fn scan_confirm(...) -> Result<...> {
    let user_id = extract_user_id(&headers)?; // 从手机端 JWT 提取身份
    match req.action.as_str() {
        "scan" => // UPDATE status = scanned, user_id = ?
        "confirm" => // UPDATE status = confirmed，桌面端下次轮询就能拿到 JWT
    }
}
```

为什么用轮询不用 WebSocket？因为扫码发生在登录前，此时桌面端还没有 WS 连接。轮询虽然有 2 秒延迟，但对于扫码场景完全够用。

---

##### 3. 前端实现

**手机端确认页**（`scan_confirm_page.dart`）， 手机扫码后跳转到这个页面。 
- 当扫到 `flashim://scan/{token}` 格式的二维码后，通过 `onScanLogin` 回调跳转到 `ScanConfirmPage`。
- 这个页面在 `initState` 时立即调用 `confirmScan(token, 'scan')` 告诉后端"我扫了"。
- 用户点确认调 `confirmScan(token, 'confirm')`，后端把状态改为 confirmed，桌面端下次轮询就拿到 JWT 了。

```dart
// initState 时标记已扫码
await authRepository.confirmScan(scanToken, 'scan');

// 用户点确认
await authRepository.confirmScan(scanToken, 'confirm');
// 桌面端下次轮询就会收到 confirmed + JWT，自动登录
```


| 移动端 - 扫码 | 移动端 - 扫码确认 |
| --- | --- |
|![Screenshot_2026-05-30-08-38-37-546_com.toly1994.flash_im.jpg](https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/0709110ccb274e0fa756c95cb4d5e7d9~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1080&h=2400&s=359368&e=jpg&b=fcfcfc)  | ![Screenshot_2026-05-30-08-42-38-412_com.toly1994.flash_im.jpg](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/133b7d0470a84b9792098f3ff9d74fd8~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1080&h=2400&s=115682&e=jpg&b=ededed) |


---

**前端核心代码**（`qr_login_form.dart`）—— 桌面端的二维码展示组件，负责创建会话、显示二维码、轮询状态、自动登录。
- `initState` 时调用 `_createSession()` 向后端请求一个 scan_token，
- 拿到 `qr_content` 后用 `qr_flutter` 包渲染二维码。
- 启动一个 `Timer.periodic`（2 秒间隔）不断轮询 `/auth/scan/status`。  
- 根据返回的状态pending、confirmed、expired 切换 UI 表现。

pending 显示二维码、scanned 显示"已扫码等待确认"、confirmed 调用 `onLoginSuccess` 回调完成登录、expired 显示过期遮罩和刷新按钮。`dispose` 时取消 Timer，避免内存泄漏。

![image.png](https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/e715db6196a84394b9ae97f298ac0357~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1059&h=741&s=149167&e=png&b=e7f1fc)


```dart
class QrLoginForm extends StatefulWidget { ... }

class _QrLoginFormState extends State<QrLoginForm> {
  Timer? _pollTimer;

  Future<void> _createSession() async {
    final result = await authRepository.createScanSession();
    setState(() { _qrContent = result.qrContent; });
    _startPolling(); // 开始每 2 秒轮询
  }

  Future<void> _pollStatus() async {
    final result = await authRepository.getScanStatus(_scanToken!);
    switch (result.status) {
      case 'scanned': setState(() => _status = 'scanned');
      case 'confirmed':
        _pollTimer?.cancel();
        widget.onLoginSuccess(LoginResult(token: result.token!, ...));
      case 'expired': _pollTimer?.cancel(); // 显示刷新按钮
    }
  }
}
```


整个流程的关键设计：桌面端和手机端不直接通信，而是通过后端的 `scan_sessions` 表做状态中转。桌面端只管轮询，手机端只管改状态，后端负责签发 JWT。三方解耦，逻辑清晰。

---


#### 五、本章总结

这一章做了两件事：把闪讯装进 Windows、给桌面端登录页做了一次大改版。

Windows 构建本身非常简单——`flutter build windows` 一条命令，产物直接能跑。分发也简单，要么 MSIX 上 Store，要么 Inno Setup 打个安装包。没有 macOS 那套签名公证的复杂流程。

登录页的改版是这一章的重头戏。左右分栏布局让桌面端终于有了"桌面应用"的感觉，不再是一个被拉宽的手机界面。扫码登录解决了桌面端没有三方登录的问题——用户只需要手机扫一下，比输密码还快。

架构上也做了一些清理：ScanPage 迁移到共享模块、WindowsButtons 组件化、登录页拆分为独立文件。这些看似小事，但随着桌面端功能越来越多，模块边界清晰的价值会越来越明显。

回头看这个项目从开始到现在，闪讯已经从一个"能发消息"的原型，长成了一个覆盖 Android、iOS、macOS、Windows、四大主流个平台的完整应用。每一章加一点功能、多一个平台、清理一些技术债。就像养一棵树，不是一夜之间长大的，而是每天浇一点水、修一下枝。

有时候回看早期的代码会觉得粗糙，但那正是成长的痕迹。重要的不是一开始就写出完美的架构，而是在每一次迭代中让它变得更好一点。这个项目教会我的最重要的事情是：**持续迭代比一步到位更可靠**。先跑起来，再跑得好，最后跑得优雅。下一章，我们来看看另一个比较冷门的桌面端 ： `Linux 产品的构建`。


