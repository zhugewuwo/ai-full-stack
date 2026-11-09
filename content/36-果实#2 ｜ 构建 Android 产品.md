---
theme: cyanosis
---

上一篇我们把后端部署到了云服务器，闪讯的"大脑"已经 7×24 小时在线了。但其他用户想要访问，需要一个装在手机里的 App 应用程序。这一篇，我们来把闪讯打包成一个真正的 Android 应用产品。围绕以下几个点展开:

- 如何设置应用的名称和图标。
- 如何打包构建 Android 应用产物，并进行尺寸瘦身。
- 签名和发布到市场的准备和流程。
- 用户协议与隐私政策、用户注销申请。
- 优化登录方式 `github登录`、设置界面优化。 (顺便新增功能)

---

#### 一、产物的形式

在开发阶段，我们一直用 `flutter run` 把应用跑在模拟器或真机上。但这种方式有个问题：它依赖你的电脑，依赖 USB 线，依赖开发环境。你没法把它发给朋友装，使用安卓手机的朋友，可能会从软件商店或者网上下载 apk 的安装包。第一阶段，我们先打包出一个能用的安装包。

---

##### 1. 构建前的代码准备

在构建之前，我们需要更新一下 `名称和图标`，因为目前还是 Flutter 的默认图标，以及 flash_im 名称。


| 修改前 |  |
| --- | --- |
| ![image.png](https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/e5ad15a68f794a939ac14789b37af9a4~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=250&h=250&s=54816&e=png&b=fdfbfb) | ![image.png](https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/3aa5225b3ce6479f903af47d97a2b4d4~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=250&h=249&s=76579&e=png&b=905f4d) |

下面的修改都可以交给 AI 来处理，文中写出来只是强调一下：

- Android 应用的名称可以修改文件：`client/android/app/src/main/AndroidManifest.xml`

```xml
<application
    android:label="闪讯"
    ...>
```

- 图标可以使用 `flutter_launcher_icons` 插件自动处理。

**步骤 1**：准备一张 512×512 以上的 logo 图片，放到 `client/assets/images/logo.png`

**步骤 2**：在 `client/pubspec.yaml` 的 `dev_dependencies` 中添加：

```yaml
flutter_launcher_icons: ^0.14.0
```

并在 pubspec.yaml 末尾添加配置：

```yaml
flutter_launcher_icons:
  android: true
  ios: true
  image_path: "assets/images/logo.png"
```
- 并在 pubspec.yaml 末尾添加配置：

```yaml
flutter_launcher_icons:
  android: true
  ios: true
  image_path: "assets/images/logo.png"
```


**步骤 3**：运行生成命令：

```bash
cd client
flutter pub get
dart run flutter_launcher_icons
```

这样会在 `client\android\app\src\main\res` 文件夹下，自动生成对应的 logo 图片。现在运行项目，就可以看到应用 logo 和 名字变化了。

![image.png](https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/ad8586b38d5e4ebd9343749ac5d282d1~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=827&h=503&s=24569&e=png&b=f1f0f3)

---

##### 2. 打包应用

最简单的打包方式是在前端项目的命令行中，使用 Flutter 命令来打包: 

```
cd client 
flutter build apk -v
```

这就是最终的产物，把它发送给你的朋友，安装后，你们就可以聊天了。


![image.png](https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/59342f32e15943b28a85b0ec6bc2ff69~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=876&h=204&s=37108&e=png&b=f2f1f4)

---

##### 3. 打包环境配置

还记得吗? 我们后端有 `.env` 来配置端口号、数据库链接等固定的值。Flutter 这里的服务器 ip 和端口号还是写死在代码里的。另外开发环境和线上环境不一样，这会导致频繁修改，如果发布时忘记改回来，那闪讯对外就完全不可用了。所以我们需要优化一下，如何区分环境进行运行和打包。  

Flutter 支持打包盒运行时传入 `--dart-define-from-file` 置顶配置文件。于是我们可以准备两套环境，运行打包时指定一下，就可以动态控制代码。这样就从 `改代码` 变成了 `改配置` : 

![image.png](https://p6-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/59beb29a004b4eef9e1a1c3eefaad6ca~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1063&h=264&s=38360&e=png&b=f0eef2)

```dart
class AppConfig {
  static const String host = String.fromEnvironment('SERVER_HOST', defaultValue: '192.168.1.75');
  static const int port = int.fromEnvironment('SERVER_PORT', defaultValue: 9600);
  static String get baseUrl => 'http://$host:$port';
}
```

比如打包发布版本的包，可以使用: 

> flutter build apk --release --dart-define-from-file=.env.production


开发阶段，使用 `.env.dev` 的配置：
> flutter run --dart-define-from-file=.env.dev

---

##### 4. 关于 CPU 架构产物

查看一下刚才命令行直接打包的产物体积，会发现 `lib` 占了 92.5% 。 里面有着三个文件夹：

![image.png](https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/aaa801d0b73d4c7a8fee2692010704cb~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=887&h=366&s=40542&e=png&b=f4f6fa)


关键在于 **CPU 架构** ， Android 手机的处理器有不同的指令集，就像不同国家说不同的语言：

| 架构 | 代号 | 对应设备 |
|------|------|---------|
| 64 位 ARM | arm64-v8a | 2017 年后几乎所有手机 |
| 32 位 ARM | armeabi-v7a | 2016 年前的老旧设备 |
| x86_64 | x86_64 | 部分模拟器 |

Flutter 默认构建的是 **fat APK**（胖包）：把三种架构的机器码全部塞进一个包里。  
三套 .so 文件，每套都是完整的引擎 + 业务代码。这就是为什么 30 MB 的东西变成了 80 MB。

> 比如你要去俄国旅行，行李箱里却同时装了俄语词典、法语词典、德语词典。到了俄本只用得上俄语那本，另外两本白白占空间。

---

首先，x86_64 版的模拟器安装包应该要去掉，用户一般都使用真机，没有必要为了模拟器增加三分之一的软件包大小。其次，目前 `arm64-v8a` 设备占比超过 95% ，剩余的都是近十年前的存量低端机，是否为了支持 `armeabi-v7a` 增加三分之一的软件包大小，也需要你权衡。

Flutter 命令提供了 `--split-per-abi` 的参数，用于把安装包按架构拆分成独立的包：

> flutter build apk --release --target-platform android-arm64,android-arm --split-per-abi --dart-define-from-file=.env.production

这样拆成两个包，大小都在 30M 一下。低端机可以通过下载对于的安装包来使用。

![image.png](https://p6-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/2696350a585f49258adb30ff816e3c21~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=746&h=103&s=15583&e=png&b=f2f1f4)

---

##### 5. APP 大小进一步优化

 `--split-per-abi` 把应用大小减到了 `29.1MB` ，但是依然还有优化的空间。
 
 > [tasks_app_size.md]() 是我让 AI 搜索一下，常规的安卓体积包优化方案，  
 > 再让它基于当前项目，给出的优化任务。

执行完后，可以发现，体积包直接减半，来到了 `14.3MB` :
 
![image.png](https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/950cb4aaf96d4f6e98048003bbdb443a~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=716&h=77&s=12181&e=png&b=f2f1f4)



---

##### 6. 构建脚本

目前 Flutter 打包安卓的命令越来越长，而且还需要区分环境。为了更方便打包流程，另外也可以顺便维护一下打包产物：

> [build_android.py]() 就是打包安卓的脚本。未来不同的平台打包，使用专门的脚本处理。包括服务端的打包构建。

![image.png](https://p6-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/6bbaa55a667c4f6e9e18e4db4945f791~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1341&h=617&s=143715&e=png&b=f1f0f3)


---

#### 二、应用整体功能优化

发布到商店之前，最后进行一下合规的处理，比如用户协议、隐私政策的展示等；另外设置页页趁此优化一下。这里把它视为一个新的功能迭代，在 `v0.24.0` 上开发。



| 模块名              | 功能分析                                                                                                                    | 前端设计                                                                                                                       | 前端任务                                                                                                                     | 
| ---------------- | ----------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| starter/v0.0.2 | [analysis.md](https://github.com/toly1994328/flash_im_by_ai/blob/master/docs/features/starter/v0.0.2/analysis.md) | [design.md](https://github.com/toly1994328/flash_im_by_ai/blob/master/docs/features/starter/v0.0.2/client/design.md) | [tasks.md](https://github.com/toly1994328/flash_im_by_ai/blob/master/docs/features/starter/v0.0.2/client/tasks.md) | 
---


##### 1. 用户协议、隐私政策

用户协议和隐私政策是 APP 想上架商店必须的。这里让 AI 写了一下，并放在后端的静态资源里，通过链接可以直接访问。


![image.png](https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/aebfb4b138dc42758cb4b59833d1f615~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=546&h=249&s=11736&e=png&b=f0eff2)

前端需要在应用启动时，检测有没有同意时弹出引导。点击时通过 webview 承载展示对于的静态网页。

| 启动 | 用户协议 | 隐私政策 |
| --- | --- |--- |
| ![image.png](https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/f0bc35837d7345548635e2444ce7dd78~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1080&h=2400&s=129796&e=png&b=757575) | ![image.png](https://p6-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/94a223b126f24799aedd61e1862de8fa~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1080&h=2400&s=276520&e=png&b=fefefe) | ![image.png](https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/b050cb821dc64c8b99db9af1ea24715e~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1080&h=2400&s=282511&e=png&b=fefefe)


---

另外，在 v0.23.0 的功能迭代上，我增加了一个 github 登录的功能，并且优化了一下登录界面的表现。当没有勾选时，会先拦截，给出提示信息：


| 模块名              | 功能分析                                                                                                                    | 前端设计                                                                                                                       | 前端任务                                                                                                                     | 后端设计                                                                                                                       | 后端任务                                                                                                                     |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| auth/v0.0.3 | [analysis.md](https://github.com/toly1994328/flash_im_by_ai/tree/master/docs/features/auth/v0.0.3/analysis.md) | [design.md](https://github.com/toly1994328/flash_im_by_ai/tree/master/docs/features/auth/v0.0.3/client/design.md) | [tasks.md](https://github.com/toly1994328/flash_im_by_ai/tree/master/docs/features/auth/v0.0.3/client/tasks.md) | [design.md](https://github.com/toly1994328/flash_im_by_ai/tree/master/docs/features/auth/v0.0.3/server/design.md) | [tasks.md](https://github.com/toly1994328/flash_im_by_ai/tree/master/docs/features/auth/v0.0.3/server/tasks.md) |


---


| 登录界面 | 校验是否同意 | 设置界面增加入口 |
| --- | --- | --- |
| ![image.png](https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/e8938d9a9ec043a08efcf46034341860~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1080&h=2400&s=130409&e=png&b=ffffff)  | ![image.png](https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/b0bb4a93aa184927adb68de6c804b883~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1080&h=2400&s=143196&e=png&b=ffffff) |![image.png](https://p6-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/6fe5bc46ebc34d55a05954efb5b16ba5~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1080&h=2400&s=63527&e=png&b=f8f8f8)


---

#### 2. 设置界面整体优化

之前我的界面比较简陋，这次优化了一下。参考微信的设置，把信息集中到独立界面。并增加了账号管理、关于闪讯、我的名片等入口，看起来更正规一些。

| 我的 | 设置页 | 关于闪讯 |
| --- | --- |--- |
| ![image.png](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/c0e7cfe1ae1543369201a4c28773d066~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1080&h=2400&s=60344&e=png&b=f4f4f4) | ![image.png](https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/3cd84b433199492bbfbbb4020e745dc0~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1080&h=2400&s=63813&e=png&b=f8f8f8) |![image.png](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/4e6d6849089d4a66bd395c0a8489dc6a~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1080&h=2400&s=126035&e=png&b=f6f6f6)|


---


#### 三、别人如何下载应用

构建出了产物，下面一个问题就是: `如何让别人能得到产物`。毕竟直接发送安装给别人，是很难传播的。有两条路可以走: 

- **正规路线**: 最好的方式是上架到应用市场里，这样任何人可以直接搜索，下载你的软件，也更。
- **野生路线**: 在 github 上给下载方式、或搭建一个网页，展示你的产品，并附带下载链接。

这两条路都可以走，但野生的比较简单，完全可以自主控制。正规路线上架的流程可以说会非常坎坷，甚至是上不了架。特别是对于个人开发者。

---

##### 1. 应用的签名

正规路线需要对应用进行签名，才能上架。我们可以使用 JDK 自带的 `keytool` 来生产相关的文件。如下所示：（如果找不到 JDK 在哪里，可以让 AI 帮你搜一下）

```
cd client/android
& "C:\toly\Soft\IDE\AS2025\jbr\bin\keytool.exe" -genkey -v -keystore flash-im-release.jks -keyalg RSA -keysize 2048 -validity 10000 -alias flash-im
```

然后会让你输入一个密码，可以随便输一个。这个密码将和生成的 `flash-im-release.jks` 绑定，后面打包时需要用到。后面的一系列问题，直接 `enter` 进入下一步即可。最后一步输入 `y` 确认：

![image.png](https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/16bc9789f83049c49bc2cd336f93fc82~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=849&h=440&s=68013&e=png&b=f2f1f4)

会生成一个 `flash-im-release.jks` 文件，然后把密码给 AI ，让它为你生成 `key.properties` 的配置信息，已经配置项目的构建逻辑：

![image.png](https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/59ca115fd15b4785bb576fe81c130636~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=684&h=247&s=17133&e=png&b=f1f0f3)


---



##### 2. 打包谷歌版产物

目前我的 FlutterUnit 已经上架了谷歌商店，对上架谷歌的流程还是比较清楚的。

![image.png](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/c6603be6d4844780806a9d4c30aeff04~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1102&h=141&s=23544&e=png&b=ffffff)

Android 的安装包有两种格式，上架到谷歌需要打 `aab` 的包：

| 格式 | 后缀 | 说明 |
|------|------|------|
| APK | `.apk` | 传统安装包，可以直接安装，适合分发给朋友 |
| AAB | `.aab` | Google Play 专用格式，上架应用商店用 |

构建脚本增加 `--aab` 即可打包 aab 的产物：

> python scripts/build_center/build_android.py --aab


![image.png](https://p6-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/4fd95a09234d4b9caea75939808411c4~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=947&h=223&s=37377&e=png&b=f2f1f4)

AAB 不是直接给用户安装的包，而是交给 Google Play 的"半成品"。Google Play 会根据每个用户的手机型号，动态裁剪出最小的 APK 推送给他。

- arm64 的手机只收到 arm64 的代码
- 高分辨率手机只收到高清资源
- 中文用户只收到中文语言包

虽然现在看着是 56.1MB，但最终用户下载的体积可能只有 25~30 MB。

---

##### 3. 谷歌商店上架

首先你需要成为谷歌开发者，这一步需要交 $25，一次性的永久生效。

> 接入控制台: https://play.google.com/console  
> 首页/创建应用 ，提交基本信息

![image.png](https://p6-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/d1fdce1a36f54417a71f451b3ebf9348~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1512&h=1093&s=133996&e=png&b=f7f9fd)

---

个人开发者需要上架谷歌商店，需要 `至少12名、14 天` 的封闭测试:

![image.png](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/7b7191e2e94344edbb4f3cccea8b6345~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1643&h=583&s=123446&e=png&b=ffffff)

> 测试和发布/测试/封闭式测试/创建轨道/创建新的发布版

然后把打的包上传一下就行了：

![image.png](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/e9cf435bf44b4eb3b2aa889643a42100~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=2011&h=536&s=46124&e=png&b=ffffff)

后续的测试、审核过程就需要大家自己去持续关注了。另外国内也有很多商店，比如华为、小米、OPPO等，需要上架还需要软著、经营证件等，基本上个人开发者很难上架，如果有小公司大家也可以去折腾一下。

---

##### 4. 野生路线

野生路线其实，你只要将打包的 apk 丢到一个可供下载的地方即可。也不一定非要丢到自己的服务器上，毕竟占空间、下载也耗流量。很多开源软件都会在 github 的 release 页面给出对于的安装包。

![image.png](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/a592faf8efc24132801e9555bd51d79e~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1478&h=591&s=120571&e=png&b=ffffff)

在 Assets 下，别人就可以下载对应的安装包了。后续脚本还可以支持一下，自动发布 release 和上传安装包，这样升级就更加方便。

![image.png](https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/6fa024dea4e24c7c959f640e0ceb7ea9~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=963&h=222&s=23049&e=png&b=ffffff)

---

#### 四、本章总结

走到这里，闪讯已经从一个"只能连着电脑跑"的工程项目，变成了一个可以发给朋友装在手机里的真实产品。回头看这个过程，其实就做了几件事：把代码变成安装包、把安装包瘦身、给安装包盖个章（签名）、然后想办法递到用户手里。每一步都不难，但串起来就是一个完整的"从开发者到用户"的旅程。

有几个感受分享一下：

- **体积优化比想象中简单。** 80 MB 听起来很吓人，但其实不是你代码写多了，而是打包机制默认把同样的东西复制了好几份。知道原因后，一两行配置就能砍掉一半。
- **签名没那么神秘。** 本质就是一把钥匙，证明"这个包确实是你发的"。一条命令生成，四行配置引用，仅此而已。  
- **分发才是真正的挑战。** 技术上构建一个 APK 很快，但要让陌生人能搜到、能信任、愿意装，这背后是商店审核、合规要求、用户信任的综合考验。好在野生路线（GitHub Release）让我们可以先跑起来，不必等万事俱备。  
- **构建脚本是给未来的自己写的。** 今天记得每个参数的含义，三个月后大概率忘光。把它固化成脚本，下次一行命令就好，不用再翻文档。

到这一步，闪讯已经是一个"能用"的产品了。接下来要做的，是让它变成一个"好用"的产品——但那是后面的故事了。下一篇，我们将焦点聚集在 iOS 产品的构件上。 
