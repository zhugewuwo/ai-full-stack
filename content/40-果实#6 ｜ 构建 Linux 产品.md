---
theme: cyanosis
---

Android、iOS、macOS、Windows 四大主流平台的打包搞定了，闪讯已经可以覆盖绝大多数用户。但还有一个群体不能忽略——Linux 桌面用户。虽然市场份额不大，但 Linux 用户往往是开发者、极客、技术决策者，他们对产品的口碑传播力不可小觑。本章围绕以下几个点展开：

- 如何在 Windows 通过 WSL2 的 Linux 构建桌面应用
- 打包 .AppImage 产物
- 桌面端界面的适配，更好地符合用户体验。

> Flutter 的 Linux 桌面支持已经 stable，同一套代码无需修改即可编译为原生 Linux 应用。

Linux 桌面端构建，在 `v0.28.0` 迭代里，模块是 `ui/desktop/v0.0.2`

| 模块名 | 功能分析 | 前端设计 | 前端任务 |
| --- | --- | --- | --- |
| ui/desktop/v0.0.2 | [analysis.md](https://github.com/toly1994328/flash_im_by_ai/tree/master/docs/features/ui/desktop/v0.0.2/analysis.md) | [design.md](https://github.com/toly1994328/flash_im_by_ai/tree/master/docs/features/ui/desktop/v0.0.2/client/design.md) | [tasks.md](https://github.com/toly1994328/flash_im_by_ai/tree/master/docs/features/ui/desktop/v0.0.2/client/tasks.md) |

---


#### 一、环境准备：在 Windows 上构建 Linux

在 Windows 上构建 Linux 应用听起来有点矛盾。但 WSL2（Windows Subsystem for Linux 2）让这件事变得理所当然。它不是模拟器，而是一个跑在 Windows 里的真正 Linux 内核，性能接近原生。如果你有 Linux 平台的设备，那可以省去准备 Linux 平台这一步。

---

##### 1. 确认 WSL2 已就绪

Windows 11 自带 WSLg（Linux GUI 支持），可以直接在 Windows 桌面上显示 Linux 应用窗口——这意味着你构建完 Linux 版闪讯后，能直接在 Windows 桌面上看到它跑起来。

```powershell
# PowerShell 中检查
wsl --version

WSL 版本: 2.6.3.0
内核版本: 6.6.87.2-1
WSLg 版本: 1.0.71
MSRDC 版本: 1.2.6353
Direct3D 版本: 1.611.1-81528511
DXCore 版本: 10.0.26100.1-240331-1435.ge-release
Windows: 10.0.26200.8457
```

如果没装过，一条命令搞定：

```powershell
wsl --install -d Ubuntu-22.04
```

---


##### 2. 安装构建依赖

Flutter Linux 桌面应用基于 GTK，构建需要一套 C/C++ 工具链：

```bash
sudo apt update
sudo apt install -y clang cmake ninja-build pkg-config libgtk-3-dev
```

目前项目用到了视频缩略图（fc_native_video_thumbnail），还需要 FFmpeg 开发库：

```bash
sudo apt install -y libavcodec-dev libavformat-dev libavutil-dev libswscale-dev libavfilter-dev
```

可以安装一下中文字体，否则界面上所有中文都是方块：

```bash
sudo apt install -y fonts-noto-cjk
```

drift 本地数据库需要安装一下 SQLite3：

```bash
sudo apt install -y libsqlite3-dev
```

---

##### 3. 安装 Linux 版 Flutter SDK

在 WSL 里装一个 Linux 原生的 Flutter SDK，下面的命令会现在 Flutter 3.44.0 版本: 

```bash
cd ~
mkdir -p SDK && cd SDK
wget https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_3.44.0-stable.tar.xz
tar xf flutter_linux_3.44.0-stable.tar.xz
```

这里有个容易踩的坑：WSL 的 PATH 会继承 Windows 的环境变量，直接输入 `flutter` 可能调用的是 Windows 版。Windows 版 Flutter 在 Linux 里运行会报 `bash\r: No such file or directory`，Windows 换行符惹的祸。可以把这里的 Flutter PATH 放在最前面优先使用：

```bash
echo 'export PATH="$HOME/SDK/flutter/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

验证一下 Linux 环境下的 Flutter 命令：

```bash
which flutter
# /home/toly/SDK/flutter/bin/flutter

flutter doctor
# [✓] Flutter  [✓] Linux toolchain
```

---

#### 二、构建与运行

环境就绪，接下来就是 Flutter 最擅长的事，一条命令出产物。

---

##### 1. 解决 /mnt/c 的权限问题

WSL 访问 Windows 文件系统（`/mnt/c/...`）时，文件权限模型和 Linux 原生不同。Flutter 构建过程中 CMake 的 install 步骤需要设置文件权限，在 `/mnt/c` 上会报 "Permission denied"。

解决方案很优雅：用符号链接把 build 输出目录指向 WSL 原生文件系统：

```bash
cd /mnt/c/toly/Project/AIGC/flash_im_v1/client
rm -rf build/linux
mkdir -p ~/flash_build/linux
ln -s ~/flash_build/linux build/linux
```

源码还在 Windows 上（方便用编辑器），构建产物写到 WSL 原生路径（有完整 Linux 权限）。两全其美。

---

##### 2. 开发运行

命令中只需要指定 `-d linux` 即可：

```bash
cd /mnt/c/toly/Project/AIGC/flash_im_v1/client
flutter pub get
flutter run -d linux --dart-define-from-file=.env.dev
```


WSLg 会自动把 Linux GUI 窗口显示在 Windows 桌面上，和原生 Windows 窗口并排显示。支持热重载，体验和移动端开发一致。之前做的桌面端 UI 适配（三栏布局、侧栏浮层、弹窗化操作），在 Linux 下同样生效——毕竟是同一套代码。

| 登录页 | 消息页 |
| --- | --- |
| ![image.png](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/bb7ef39354e5417c9ee4424a73b1cdb1~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=912&h=612&s=128124&e=png&b=e5eef8) | ![image.png](https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/3019773cdd7448ffab22f508da0d808d~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1252&h=852&s=124967&e=png&b=fcfcfc) |


---


##### 3. 关于 libsqlite3 的自动打包

开发时需要 `sudo apt install libsqlite3-dev`，否则运行报 `Failed to load dynamic library 'libsqlite3.so'`。但分发给用户时不能要求他们也装这个。在 `client/linux/CMakeLists.txt` 里加了自动打包：

```cmake
find_library(SQLITE3_LIB sqlite3)
if(SQLITE3_LIB)
  install(FILES "${SQLITE3_LIB}" DESTINATION "${INSTALL_BUNDLE_LIB_DIR}"
    COMPONENT Runtime)
endif()
```

构建后 bundle 里会包含 `libsqlite3.so`，用户不需要额外安装任何依赖，下载即用。



---

##### 4. 构建 release

```bash
flutter build linux --release --dart-define-from-file=.env.production
```

产物在 `build/linux/x64/release/bundle/`：


![image.png](https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/13b401e3408246eda635634bdbc2fdef~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=851&h=269&s=17038&e=png&b=f2f1f4)

双击 `flash_im` 就能启动。把整个 `bundle/` 压缩发给别人，对方解压就能用。但这样不够优雅——用户还得解压、找可执行文件、设置权限。我们需要一个更好的分发方式。

---

##### 5、AppImage 打包与分发

Linux 桌面应用没有统一的"应用商店"，分发方式五花八门。对于当前阶段，**AppImage** 是最务实的选择——单个文件，任何 Linux 发行版都能跑，用户 `chmod +x` 后双击即可使用。不需要安装，不需要 root 权限，不需要处理依赖。类似 macOS 的 .app，但更轻量。

整个打包流程已经自动化，放在了 `build_linux.sh` 脚本中：

```bash
bash scripts/build_center/build_linux.sh
```


脚本做了这些事：

1. `flutter clean` + `flutter pub get`——干净构建
2. `flutter build linux --release`——编译产物
3. 准备 AppDir 结构——按 AppImage 规范组织文件
4. 创建 `.desktop` 文件——Linux 桌面快捷方式元数据
5. 创建 `AppRun` 启动脚本——设置 LD_LIBRARY_PATH
6. 下载 `appimagetool`——如果本地没有，自动从 GitHub 下载
7. 打包为 `FlashIM-x86_64.AppImage`

产物输出到 `scripts/build_center/dest/linux/flash_im.AppImage`。它就是我们要分发的 Linux 产品：

![image.png](https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/68679547a1ce4ce29eb5328007a45a11~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1153&h=153&s=24056&e=png&b=f2f1f4)

---

#### 三、桌面端的导航优化

在本章的 v0.28.0 版本迭代的重头戏是，桌面端交互体验的全面升级。让闪讯在大屏幕上真正有"桌面应用"的感觉，而不是一个被拉宽的手机界面。之前界面基本上全屏的跳转，这在桌面端的体验上可谓是灾难。本章节结合微信桌面端的交互，优化一下闪讯在桌面端的某些体验。

---

##### 1. 群组信息

在移动端，查看聊天详情是一个很自然的操作：点击右上角按钮，全屏跳转到详情页，看完按返回键回来。  
但在桌面端，这个交互就很别扭了。你正在看聊天记录，想瞄一眼群成员列表，结果整个聊天页面被替换成了详情页，看完还得点返回。

微信桌面端的做法是：点击右上角按钮，右侧滑出一个面板，聊天内容还在左边，详情在右边。想看就看，不想看点一下外面就收起来了，交互成本几乎为零。另外滑出的侧栏视图是和移动端一致的，可以复用之前的界面：

![image.png](https://p6-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/bfb8d8e0d2ca41179234a3e1c355a970~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1784&h=1190&s=204765&e=png&b=fdfdfd)


闪讯的实现也是这个思路，但技术细节上有几个值得展开的地方。

---

**外部点击收起**

侧栏展开后，用户点击外部的任何位置应该自动收起侧栏。传统做法是在侧栏外面盖一层半透明的 `GestureDetector`，但这样会拦截聊天区的所有手势（滚动、长按、点击消息等）。

Flutter 3.10+ 提供了 `TapRegion` 组件，它能检测"点击发生在自身区域之外"的事件，不需要额外的遮罩层，不会拦截其他手势：

```dart
TapRegion(
  onTapOutside: _showChatDetail
      ? (_) => _toggleChatDetail()
      : null,
  child: /* 侧栏内容 */,
)
```

一行代码搞定。侧栏内部的点击（滚动列表、点击按钮）不会触发 `onTapOutside`，只有点击侧栏外面才会。

---

**局部导航栈**


侧栏里显示的是群详情页或单聊详情页，这些页面内部有很多操作：邀请入群、踢人、编辑群名、查找聊天内容。如果不做特殊处理，这些操作的 `Navigator.push` 会走外层 Navigator，仍然会导致进入一个全屏的界面。如果一个个修改适配的话，工作量又会非常大。解决方案是给侧栏套一个独立的 `Navigator`：

![image.png](https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/a161ec8ffc7b44a6b895ddd621dfdbca~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1784&h=1190&s=194163&e=png&b=fdfdfd)

```dart
class ChatDetailSidebar extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Navigator(
      key: ValueKey('detail_${conversation.id}'),
      onGenerateRoute: (_) => MaterialPageRoute(
        builder: (navContext) {
          if (conversation.isGroup) {
            return GroupChatInfoPage(
              showAppBar: false,
              onSearchChat: () => _pushSearch(navContext, context),
              ...
            );
          }
          return PrivateChatInfoPage(showAppBar: false, ...);
        },
      ),
    );
  }
}
```

这样侧栏内的所有 `Navigator.push` 都在 320px 的区域内完成页面跳转，体感和移动端是一致的。比如用户在侧栏里点"查找聊天内容"，搜索页会在侧栏内打开（带返回按钮），而不是全屏跳转。

---

##### 2. 弹窗化操作

桌面端的另一个大问题是：很多操作在移动端是全屏页面（发起群聊、加好友、综合搜索），但在桌面端全屏跳转会让用户丢失当前上下文。解决方案是把这些操作改为弹窗形式。


![image.png](https://p6-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/e5163a28413944c99df2683f8a438529~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1784&h=1190&s=186188&e=png&b=757575)


每个弹窗内部都有独立的 Navigator，可以保证子页面跳转不会跳出弹窗：

```dart
void showAddFriendDialog(BuildContext ctx) {
  final screenHeight = MediaQuery.of(ctx).size.height;
  final dialogHeight = (screenHeight * 0.8).clamp(0.0, 800.0);
  showDialog(
    context: ctx,
    builder: (_) => Dialog(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(12),
        child: SizedBox(
          width: 420,
          height: dialogHeight,
          child: Navigator(
            onGenerateRoute: (_) => MaterialPageRoute(
              builder: (_) => UserSearchPage(
                repository: ctx.read<FriendRepository>(),
              ),
            ),
          ),
        ),
      ),
    ),
  );
}
```

比如"加好友"弹窗里搜索到一个用户，点击查看资料，资料页会在弹窗内打开（带返回按钮）。用户始终在 420×80% 的弹窗范围内操作，不会跳出去。

---

##### 3、其他界面的桌面端视频

之前的通讯录 Tab 点击"新的朋友"、"群通知"、"群聊"、用户都是全屏跳转。在桌面端，这些应该在右侧面板直接显示。

![image.png](https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/d6750ffd35b7441fb3c81c60d3d9f05e~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1784&h=1190&s=96030&e=png&b=fefefe)

另外，我的界面也把设置和个人信息简单整合了一些。后面有时间也可以更细致地进行设计。

![image.png](https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/f5fd05d337e94a93860bae60a2faa7c5~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1784&h=1190&s=75725&e=png&b=f8f8f8)

侧边栏底部的按钮，参考微信弹出操作菜单。这里使用了我的 tolyui 中的 [tolyui_navigation](https://pub.dev/packages/tolyui_navigation) 组件实现。

![image.png](https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/13043bbbcb6e4f859331c8bf28adf7c8~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1784&h=1190&s=179178&e=png&b=fefefe)


最后还增加了意见反馈的小功能，会把用户输入的信息发送给闪讯团队的会话。虽然小，但涉及了完整的前端闭环：UI 输入 → 创建会话 → 发送消息 → 激活会话。


| 意见反馈 | 发送消息 |
| --- | --- |
| ![image.png](https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/9a3d16540c874eaa8d729fdac047735b~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1784&h=1190&s=147335&e=png&b=757575) | ![image.png](https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/648cc6d1e4144a2b9e3eb3bcb7e90948~tplv-k3u1fbpfcp-jj-mark:0:0:0:0:q75.image#?w=1784&h=1190&s=171751&e=png&b=fefefe) |


---

#### 四、本章总结

Linux 桌面端的构建，技术上比 macOS 和 Windows 都简单。没有签名证书、没有公证流程、没有 Inno Setup。`flutter build linux` 一条命令出产物，`appimagetool` 一条命令打包。真正花时间的是 WSL 环境搭建、权限、Flutter SDK 版本这些琐碎问题。

但一旦环境搞定，后续的迭代就是无脑执行脚本的事。`bash scripts/build_center/build_linux.sh`，等几分钟，拿到 AppImage，发给用户。

至此，闪讯已经覆盖了 **Android、iOS、macOS、Windows、Linux** 五大平台。同一套 Dart 代码，同一套业务逻辑，只是 UI 层根据平台做了适配（移动端底部导航 + 全屏跳转，桌面端侧边栏 + 三栏布局 + 弹窗化操作）。这就是 Flutter 跨平台的价值，不是"一次编写到处运行"的理想主义，而是"一次编写，每个平台微调一下就能用"的务实主义。

回头看这个项目的桌面端演进：v0.26.0 做了基础的三栏布局和响应式切换，v0.27.0 加了扫码登录和 Windows 构建，v0.28.0 把交互体验打磨到了可用的程度。三个版本，从"能看"到"能用"到"好用"。每一步都不大，但累积起来差距很明显。

后续可以做的事情还有很多：侧栏宽度可拖拽、快捷键支持、系统托盘、桌面通知。但那些是锦上添花的事，当前的基础已经足够支撑日常使用了。
