---
theme: cyanosis
---

Android、iOS 两个移动端版本搞定了，但闪讯是一个 IM 应用——用户在电脑上打字聊天的需求可能比手机还强。这篇来聊聊如何把 Flutter 项目构建成 macOS **桌面应用**，以及两种分发方式：`Mac App Store` 和 `dmg文件` 网络分发。本章围绕以下几个点展开:


- 如何打包构建 macOS 应用产物。
- 发布到 Apple 应用市场的准备和流程。
- 签名、打包 dmg、公证，自动化构建脚本
- 初步优化桌面端 UI 界面布局


> Flutter 的 macOS 支持已经 stable，同一套代码无需修改即可编译为原生 macOS 应用。


---

#### 一、构建 macOS 产物的前置准备

同样是 Apple 生态，macOS 和 iOS 构建有不少相似之处，但也有关键差别：

| 对比项 | iOS | macOS |
|--------|-----|-------|
| 构建命令 | `flutter build ipa` | `flutter build macos` |
| 产物格式 | .ipa | .app（可打包为 .dmg） |
| 分发方式 | App Store / TestFlight | App Store / DMG / 直接拷贝 |
| 沙盒 | 强制 | 可选（App Store 强制） |
| 签名要求 | 必须 | App Store 必须，DMG 分发建议 |
| 网络权限 | 默认允许 | 需要在 entitlements 中声明 |

一句话：macOS 比 iOS 自由得多，你可以绕过 App Store 直接分发。如果你上一章 iOS 的环境没问题，那么本章 macOS 应该会很顺利。

---

##### 1. 项目 ID 和名称

**Bundle ID**（`client/macos/Runner/Configs/AppInfo.xcconfig`）：

```
PRODUCT_BUNDLE_IDENTIFIER = com.toly1994.flashIm
PRODUCT_NAME = 闪讯
```

和 iOS 共用同一个 Bundle ID，App Store Connect 会自动关联为同一个 App 的两个平台。我们在建 App 时，就准备将这两者视为一个分发：


![image.png](https://p6-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/35bf9d3bf8e44d3a8c06076efee20e36~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=940&h=333&s=58766&e=png&b=fefefe)

---

##### 2. 应用图标

**相关文件位置**（`client/macos/Runner/Assets.xcassets/AppIcon.appiconset/`）：

macOS 图标需要提供 16、32、64、128、256、512、1024 七种尺寸。准备一张 1024×1024 的 PNG 源图，让 AI 用脚本批量生成：

```python
from PIL import Image

img = Image.open("icon_1024.png")
for size in [16, 32, 64, 128, 256, 512, 1024]:
    img.resize((size, size), Image.LANCZOS).save(f"app_icon_{size}.png")
```

替换 `AppIcon.appiconset/` 下的同名文件即可。如果和 iOS 共用同一个图标，直接从 iOS 的 1024×1024 源图生成。


![image.png](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/5315b6ddd2734d49b3286b04509589a8~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=725&h=286&s=54018&e=png&b=fdfdfd)

---

##### 3. 网络权限

**相关文件位置**（`client/macos/Runner/DebugProfile.entitlements` 和 `Release.entitlements`）：

```xml
<key>com.apple.security.network.client</key>
<true/>
<key>com.apple.security.network.server</key>
<true/>
```

> 这是 macOS 和 iOS 最大的区别之一：macOS 的 App Sandbox 默认禁止网络访问，必须显式声明。忘了加这个，应用跑起来但连不上服务器。

---

##### 4. 运行项目

执行下面的命令，就可以轻松地将闪讯跑到 macOS 桌面端：

```bash
cd client
flutter run -d macos --dart-define-from-file=.env.dev
```

Flutter 会编译并直接启动一个 macOS 窗口应用。支持热重载（r）和热重启（R），开发体验和移动端一致。只不过目前存在一个比较大的问题：

> 界面整体还是移动端的样式，像是一个扁平的手机，看起来非常别扭。

这也是接下来桌面端在 UI 上需要适配优化的点，会随着本章和下几章逐步迭代。

| 登录界面 | 消息界面 |
| --- | --- |
| 
![image.png](https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/38861d1482384de8adf94f726a95ba0c~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=800&h=632&s=49726&e=png&b=ffffff) | ![image.png](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/7d18d4007f26401f9c97ef99acaed94a~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=800&h=632&s=66150&e=png&b=fcfcfc) |


---


#### 二、签名、打包 dmg 和公正

不走 App Store，直接把 .dmg 安装包放到网站上让用户下载。适合快速迭代、不想等审核的场景。这条路需要三步：**签名 → 打包 DMG → 公证**。没有签名和公证的 App，用户打开时会看到"无法验证开发者"的警告。签名 + 公证后，体验和 App Store 下载的一样丝滑。

> 下面是过程中的详细流程，但最终签名、打包 dmg 和公正最后都会通过脚本，一键处理。这里大家就当做了解一下，脚本里做了哪些事。

---

##### 1. 创建 Developer ID Application 证书

这个证书专门用于 App Store 外分发的签名，和 iOS 的 Distribution 证书不同。

**生成 CSR 文件：**

```bash
openssl req -new -newkey rsa:2048 -nodes \
  -keyout ~/devid_key.key \
  -out ~/CertificateSigningRequest.certSigningRequest \
  -subj "/emailAddress=你的邮箱/CN=你的名字/C=CN"
```


![image.png](https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/023487ae96144510a4d5ca66de7b4b7a~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=609&h=82&s=18794&e=png&b=fcfcfc)

---

**在开发者后台创建证书：**

1. 打开 [developer.apple.com/account](https://developer.apple.com/account) → Certificates → "+"
2. 选择 **Developer ID Application**

![1.png](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/9dea5fa3d07a4191bed7745d66ae8603~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=847&h=162&s=24593&e=png&b=fefefe)

3. Profile Type 选 **G2 Sub-CA (Xcode 11.4.1 or later)**
4. 上传刚才的 `.certSigningRequest` 文件
5. 下载得到 `developerID_application.cer`


![image.png](https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/4a6a63452a634a0894f84fd9338b14eb~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=672&h=79&s=11849&e=png&b=fdfdfd)

---


**导入钥匙串：**

```bash
# DER 转 PEM
openssl x509 -inform DER -in ~/Downloads/developerID_application.cer -out /tmp/devid.pem

# 合并私钥和证书为 p12（必须加 -legacy，否则 macOS 钥匙串无法识别）
openssl pkcs12 -export -inkey ~/devid_key.key -in /tmp/devid.pem \
  -out /tmp/devid.p12 -password pass:temp123 -legacy

# 导入钥匙串
security import /tmp/devid.p12 -k ~/Library/Keychains/login.keychain-db \
  -P temp123 -T /usr/bin/codesign
```

**验证：**

```bash
security find-identity -v -p codesigning | grep "Developer ID"
```

看到类似输出就说明成功了：

```
8CA4AFC7... "Developer ID Application: deli zhang (V6P5QXUH55)"
```


![3.png](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/c0027c1e071c49a7a6653584ff4ae9b8~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=709&h=275&s=84322&e=png&b=fdfdfd)

---

##### 2. 配置凭证

把签名和公证需要的信息添加到 `client/ios/.env.publish`（和 iOS 上传共用这个文件）：

```bash
# ─── macOS DMG 分发（签名 + 公证） ───
DEVELOPER_ID_SIGN_IDENTITY=Developer ID Application: deli zhang (V6P5QXUH55)
APPLE_ID=xxxx
TEAM_ID=V6P5QXUH55
APP_SPECIFIC_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

**⚠️ 关键点**：`DEVELOPER_ID_SIGN_IDENTITY` 必须是引号里的完整字符串，包含 `Developer ID Application: ` 前缀。只写名字和 TeamID 会导致签名失败。

其中 App 专用密码在 [appleid.apple.com](https://appleid.apple.com) → 登录 → App 专用密码 → 生成。


![4.png](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/37baafdaae3d48acb5cc087c3684b2b0~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1091&h=722&s=133794&e=png&b=fefefe)

---

##### 3. 签名

构建完成后，在**原始构建目录**签名（不要复制 .app 到别处再签，复制会破坏框架的符号链接结构）：

```bash
cd client/build/macos/Build/Products/Release

# 先签名所有内嵌框架
for framework in flash_im.app/Contents/Frameworks/*.framework; do
  codesign --force --options runtime --timestamp \
    --sign "Developer ID Application: deli zhang (V6P5QXUH55)" \
    "$framework"
done

# 再深度签名整个应用
codesign --force --deep --options runtime --timestamp \
  --sign "Developer ID Application: deli zhang (V6P5QXUH55)" \
  flash_im.app
```

四个参数缺一不可：
- `--force`：强制重新签名
- `--options runtime`：启用 Hardened Runtime（公证必需）
- `--timestamp`：安全时间戳（公证必需，漏掉这个公证必定失败）
- `--deep`：深度签名所有内嵌内容

---

##### 4. 打包 DMG

```bash
hdiutil create -volname "闪讯" -srcfolder flash_im.app \
  -ov -format UDZO flash_im.dmg
```

如果想要更好看的安装界面（自定义背景、图标位置、Applications 快捷方式），可以用 `create-dmg`：

```bash
brew install create-dmg

create-dmg \
  --volname "闪讯" \
  --background "background.png" \
  --window-pos 360 100 \
  --window-size 800 600 \
  --icon-size 80 \
  --icon "flash_im.app" 230 285 \
  --app-drop-link 570 285 \
  flash_im.dmg flash_im.app
```

用户打开 DMG 后看到的就是一个精心设计的安装界面，把 App 拖到 Applications 文件夹即可。

---

##### 5. 公证

公证是让 Apple 服务器扫描你的 App，确认没有恶意代码。公证通过后，macOS Gatekeeper 会信任你的 App，用户打开时不会有任何警告。

**直接对 DMG 文件公证**（不需要压缩成 ZIP）：

```bash
xcrun notarytool submit flash_im.dmg \
  --apple-id "1981462002@qq.com" \
  --team-id "V6P5QXUH55" \
  --password "你的App专用密码" \
  --wait
```

`--wait` 参数会等待 Apple 处理完成，通常 2~5 分钟。看到 `status: Accepted` 就说明公证成功了。

如果失败，查看详细日志：

```bash
xcrun notarytool log <提交ID> \
  --apple-id "..." --team-id "..." --password "..."
```

---

##### 6. 一键构建脚本

上面的流程已经封装成了脚本，一条命令搞定。脚本位置在项目的 `scripts/build_center/build_macos.py`

```bash
python3 scripts/build_center/build_macos.py --dmg
```

脚本会自动：构建 → 签名 → 打包 DMG → 公证。产物在 `scripts/build_center/dest/macos/flash_im.dmg`。把它给你的朋友，就可以得到如下的效果，拖入 Appications 里就可以使用了：


![image.png](https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/84d9414f92d84109981829b31655b337~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=800&h=600&s=222533&e=png&b=e5e9ec)

---

#### 三、分发方式一：Mac App Store

MacOS 软件和 iOS 上架流程几乎一样。在应用管理这，我就是使用的一个 APP ID， 同时分发 iOS 和 MacOS ：


![image.png](https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/97437d3572d54ed982b3725ca45c2e7c~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=856&h=311&s=43490&e=png&b=fefefe)

---

##### 1. CSR 证书 和 Profiles 配置文件 

macOS 上架的证书方面要麻烦一点。可以用刚才生成的 CSR 文件，再创建两个证书：

1. 打开 [developer.apple.com/account](https://developer.apple.com/account) → Certificates → "+"  
2. 创建下载 Mac App Distribution（用于签名 App Store 版本的 .app）  
3. 创建下载 Mac Installer Distribution（用于签名 .pkg）


![image.png](https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/6cb0a68be21c4d62812879609150f638~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=599&h=65&s=7010&e=png&b=fdfdfd)

创建时上传你之前生成的同一个 CSR 文件（~/CertificateSigningRequest.certSigningRequest），下载后让 AI 遍历导入钥匙串即可。


---

另外，实际上传时报了一些错误，AI 分析后，表示需要安装对应的 profiles 文件：

![image.png](https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/99777986ccf64cadad39dc661353e582~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=914&h=246&s=24236&e=png&b=fefefe)

1. 打开 [profiles 配置](https://developer.apple.com/account/resources/profiles) → ## Profiles → "+"  
2. 选 Mac App Store Connect
3. App ID 选 com.toly1994.flashIm  

下载 .mobileprovision 文件，让 AI 为你安装


![image.png](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/8a54498b9c97408ebae9885e654a975e~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=585&h=73&s=12225&e=png&b=fdfdfd)


---

##### 2. Xcode 手动签名

打开 `client/macos/Runner.xcworkspace`，在 Signing & Capabilities 中：
- 取消勾选 Automatically manage signing
- Team 选择你的开发者账号
- 确认 Bundle ID 是 `com.toly1994.flashIm`
- Signing Certificate 选择 `3rd Party Mac Developer Application`
- Provisioning Profile 选择你创建的 macOS App Store 分发 Profile

你也可以让 AI 结合你的环境，来直接改项目里的相关文件。

---

##### 3. 编译和上传

编译和上传到 AppStore 的流程也在 `build_macos.py` 支持了，使用 `--upload` :

> python3 scripts/build_center/build_macos.py --upload 


![image.png](https://p6-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/4524680feec0422a84974024b0f7e65a~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=756&h=180&s=47353&e=png&b=211d24)

macOS App Store 审核比 iOS 宽松一些，但基本规则相同。看到 App 管理里面有对应的包，就说明整个流程是通的：


![image.png](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/13b5c8d490604d4f8051ea0dbd875a58~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=999&h=482&s=73725&e=png&b=fdfdfd)

---

#### 四、桌面端 UI 适配 - 聊天页


前面说了，直接跑起来的桌面端就是一个扁平的手机界面，非常别扭。想象一下你打开微信桌面版，结果看到的是手机版微信被拉宽了——底部导航栏还在，点一个会话整个屏幕都跳走了。这显然不是桌面端用户期望的体验。  
桌面端用户期望的是什么？**左边看列表，右边看内容，不用来回跳**。微信、Telegram、Discord 都是这个模式。所以这一版我们要做的核心事情就是：把移动端的"全屏跳转"改成桌面端的"分栏展示"。


![image.png](https://p6-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/35367c2376ec4e0b8dc3d09a03212cff~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1209&h=815&s=144323&e=png&b=fcfcfc)



> 这次迭代主要针对**聊天页**的桌面端适配——三栏布局、嵌入式聊天、桌面端输入框。通讯录、好友详情、群管理等其他页面的桌面端适配会在后续版本逐步迭代。


macOS 桌面端构建与 UI 适配，在 `v0.26.0` 迭代里，模块是 `ui/desktop/v0.0.1`

| 模块名 | 功能分析 | 前端设计 | 前端任务 |
| --- | --- | --- | --- |
| ui/desktop/v0.0.1 | [analysis.md](https://github.com/toly1994328/flash_im_by_ai/tree/master/docs/features/ui/desktop/v0.0.1/analysis.md) | [design.md](https://github.com/toly1994328/flash_im_by_ai/tree/master/docs/features/ui/desktop/v0.0.1/client/design.md) | [tasks.md](https://github.com/toly1994328/flash_im_by_ai/tree/master/docs/features/ui/desktop/v0.0.1/client/tasks.md) |

---

##### 1. 响应式布局：一套代码，两种形态

第一个问题是：怎么让同一份代码在手机上是底部导航，在电脑上是侧边栏？

答案是**根据窗口宽度动态切换**。我用了自己写的 `tolyui_rx_layout` 库，里面有个 `Rx$` 组件，用起来就一行：

```dart
Rx$(
  mobile: (_) => MobileLayout(homeState: this),
  desktop: (_) => DesktopLayout(homeState: this),
)
```

窗口宽了走桌面端，窄了走移动端。你甚至可以在 macOS 上拖拽窗口边缘，看着布局实时切换——这比用 `Platform.isMacOS` 判断要灵活得多，因为用户可能把窗口缩得很小。


| 桌面端-缩窄 | 桌面端-宽屏 |
| --- | --- |
|![image.png](https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/42515e969b9945269b01fe1a1832e011~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=400&h=800&s=74104&e=png&b=fcfcfc) |![image.png](https://p6-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/35367c2376ec4e0b8dc3d09a03212cff~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1209&h=815&s=144323&e=png&b=fcfcfc)

|




另外，多大宽度展示桌面端的边界值不是写死的，tolyui_rx_layout 通过 Flutter 的 `ThemeExtension` 机制全局配置。想改断点？拓展主题中改一个数字就行，所有页面自动生效。

---

##### 2. 三栏布局：参考微信桌面端

桌面端的消息页面是经典的三栏结构：

```
┌──────┬────────────┬──────────────────────────┐
│      │  Q 搜索  ⊕ │     传统色研究会      ⋯  │
│  👤  ├────────────┤                          │
│      │ 传统色研究会│   姜黄签到，中药色系代表   │
│  💬  │ 橙红色调   │                          │
│      │ 红色系家族  │   橄榄绿报到             │
│  👥  │ ...        │                          │
│      │            │   ┌──────────────────┐   │
│  ⚙️  │            │   │  输入框          │   │
│      │            │   │  😀 📷 📁       │   │
└──────┴────────────┴──┴──────────────────────┘
 68px     320px              自适应
```

- **左侧导航栏**：纯图标，不占太多空间。顶部是用户头像，中间是消息/通讯录/我三个 Tab，底部是设置按钮。
- **中间面板**：搜索栏 + 会话列表。点击会话不会跳转，而是更新右侧面板。
- **右侧聊天区**：当前选中会话的聊天内容，包括消息列表和输入框。


---


这里有个很重要的设计决策：移动端和桌面端有大量共用逻辑（打开聊天、搜索、好友详情、创建群聊...），如果各写一份就是灾难。我的做法是用 mixin 提取公共动作：

```
home/view/
├── home_page.dart          — 入口，只做 Rx$ 分发
├── home_actions_mixin.dart — 公共动作（openChat, openSearch...）
├── mobile_layout.dart      — 移动端：底部导航 + 全屏跳转
└── desktop_layout.dart     — 桌面端：侧边栏 + 分栏
```

`HomeActionsMixin` 里定义了所有业务操作，移动端和桌面端都通过 `homeState` 访问这些方法。区别只在于：
- 移动端调 `openChat()` → `Navigator.push` 全屏跳转
- 桌面端调 `buildChatPanel()` → 嵌入右侧面板

这样改一个业务逻辑，两端同时生效。不会出现"移动端修了 bug，桌面端忘了改"的情况。

---

##### 3. ChatPage 的 embedded 模式

ChatPage 原本是设计为全屏页面的——有 AppBar、有返回按钮、有 SafeArea。直接塞进右侧面板会很奇怪。
所以我给 ChatPage 加了一个 `embedded` 参数：

```dart
ChatPage(
  embedded: true,  // 桌面端面板内使用
  conversationId: conv.id,
  peerName: conv.displayName,
  ...
)
```

`embedded: true` 时：
- AppBar 变成白色背景，标题 14px 居左（不是默认的居中大标题）
- 没有返回按钮（因为不是 push 进来的）
- AppBar 区域支持拖拽移动窗口（因为隐藏了系统标题栏）
- 标题和内容之间有一条细分割线
- 底部使用桌面端专用输入框


| 桌面端-宽屏 | 桌面端/移动端-窄屏 |
| --- | --- |
| ![image.png](https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/99f72097d3414a009f58f734b032b641~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=390&h=290&s=32637&e=png&b=fcfcfc) | ![image.png](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/54441c3bbe264fdcade52ece9e303b86~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=399&h=251&s=24919&e=png&b=f9f9f9) |



注意这里的设计原则：**组件不应该知道自己在什么平台上**。`embedded` 是一个纯 UI 参数，由调用方决定传什么。这样 ChatPage 在任何地方都能复用——你甚至可以在 iPad 的分屏模式下用 `embedded: true`。

---


##### 4. IM 调色主题

做着做着发现一个问题：颜色值散落在各个文件里。侧边栏是 `0xFFEAEBF0`，搜索栏也是 `0xFFEAEBF0`，选中高亮是 `0xFFE8F0FE`... 如果以后想换个主题色，得全局搜索替换，很容易漏。

所以我做了一个 `FlashImTheme`，用 Flutter 的 `ThemeExtension` 机制：

```dart
class FlashImTheme extends ThemeExtension<FlashImTheme> {
  final Color primary;              // 主色
  final Color sidebarColor;         // 侧边栏背景
  final Color headerColor;          // 搜索栏/标题栏背景
  final Color activeConversationColor; // 会话激活高亮
  final Color navActiveColor;       // 导航图标选中背景
  ...
}
```

使用时一行代码：`context.imTheme.sidebarColor`。


![image.png](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/9ab82c548999450b85a2cb4be0b96cdb~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=596&h=164&s=23051&e=png&b=ffffff)

想颜色换肤？效果自定义的 `FlashImTheme` 配置就行。

---

##### 5. 窗口管理

最后一个细节：桌面端的窗口本身也需要管理。用 `window_manager` 插件：

```dart
if (kApp.isDesktop) {
  await windowManager.ensureInitialized();
  const windowOptions = WindowOptions(
    size: Size(1200, 800),       // 初始大小
    minimumSize: Size(400, 600), // 最小尺寸
    center: true,                // 居中显示
    titleBarStyle: TitleBarStyle.hidden, // 隐藏系统标题栏
    title: '闪讯',
  );
  await windowManager.waitUntilReadyToShow(windowOptions, () async {
    await windowManager.show();
    await windowManager.focus();
  });
}
```

隐藏了系统标题栏后，窗口怎么拖动？答案是在侧边栏和搜索栏区域加了 `DragToMoveArea`——用户拖这些区域就能移动窗口，和微信的体验一样。

---

#### 五、本章总结

这一章做了三件事：把闪讯装进 Mac、让它能分发给用户、让桌面端的界面不再像个手机。

macOS 构建本身比 iOS 简单——多了一条 DMG 分发的路，不需要审核，构建完直接发。但签名和公证的细节比较多（证书类型、时间戳、符号链接），好在最终都封装成了一条命令。

桌面端 UI 适配是一个持续的过程。这一版迭代，做了最核心的处理：三栏布局 + 嵌入式聊天 + 桌面端输入框 + 调色主题。后续还有很多可以优化的地方：快捷键、系统通知、多窗口、通讯录分栏等。但作为第一版桌面端，已经可以正常使用了。

回头看，Flutter 的跨平台能力在这里体现得很明显：同一套 Dart 业务代码，通过 mixin 共享逻辑，通过 `Rx$` 切换布局，通过 `embedded` 参数控制样式——移动端和桌面端各自有最合适的交互方式，但底层是同一个东西。这比维护两套代码强太多了。下一章，我们将聚焦另一个桌面端平台 -- **构建 Windows 应用**。

