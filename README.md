# ai-painting-help AP助手

## 使用

1.    release中下载 server.ZIP，将内容解压后的所有文件放在**与webui.bat同一个目录中**，双击start.bat启动

2. 用python直接运行

   注意aria2c需要自行前往aria2c存贮库下载 
   
   需要有python环境，**暂时不能调用ai-paint中的python环境，需要另外安装并添加到PATH**
   
   克隆仓库
   
   `git clone  https://github.com/ap-plugin/ai-paint-help.git`
   
   将ai-paint-help中所有文件放在**与webui.bat同一个目录中**
   
   执行
   
   `pip install -r requirements.txt`
   
   如果服务器在国内可以添加参数进行加速
   
   `-i https://pypi.tuna.tsinghua.edu.cn/simple`
   
   最后双击打开 **start.bat**

## **初始化**

**第一次使用将会初始化，在工作目录生成  <u>server_config.ini</u> 配置文件**

### 每个参数的含义

- **listen_port**  - AP助手的监听端口，默认6980

- **listen_address** - AP助手的监听地址，默认0.0.0.0监听所有地址

- **webui_port** - AP助手所管理的WebUI的端口地址，默认7860

- **start** - WebUI启动脚本地址，默认webui.bat

- **Authorization** - AP助手鉴权密钥，初始化时自动生成

- **rpc-listen-port** - aria2c监听端口,默认6800

- **secret** - aria2c密钥，默认为空
  
  

**若要配合aria2c使用，请修改 <u>aria2_config.conf</u> 文件，文件内已有注释**



## http请求方法

**所有请求均需要在Header中添加Authorization作为鉴权，否则返回Authorization Error**

- **/start** GET 启动

- **/stop** GET 停止   

- **/init** GET初始化，尽量不要使用，仅在AP助手出错时使用

- **/download** POST 下载模型，需要用form提交以下两个
  
  - **type** 选择下载类型，只能选择
    
    - **ckpt**  下载至 <u>models/Stable-diffusion</u>
    
    - **vae** 下载至 <u>models/VAE</u>
    
    - **emb** 下载至 *embeddings*
    
    - **lora** 下载至 *models/Lora*
  
  - **file_url** 下载文件**直链**

- **/download_status** GET 获取下载状态

- **/download_stop/gid** GET 使用gid强制停止某个任务，*（gid在上面两个的返回内容中提供）*





      
