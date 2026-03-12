from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp
from astrbot.api.event import MessageChain
from astrbot.api.message_components import File, Plain
import asyncio
from jmcomic import *
import os
import zipfile
import shutil
from pathlib import Path
import time
import img2pdf
@register("jmcomic", "luoms", "一个简单的插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
    @filter.command("jmcomic")
    async def jmcomic(self, event: AstrMessageEvent):
        message_str = event.message_str.strip()
        args = message_str.split()
       
        if len(args) < 2:
            help_text = (
                "请按格式使用：\n"
                "/jmcomic info [作品id] \n"
                "/jmcomic download [作品id]"
            )
            yield event.plain_result(help_text)
            return
        command_type = args[1]
        if command_type == "info":
            if len(args) < 3:
                    yield event.plain_result("请输入作品id：/jmcomic info [id]")
                    return
                    
            id = args[2]
            if not id.isdigit():
                    yield event.plain_result("作品ID必须是数字")
                    return
            client = JmOption.default().new_jm_client()

# 本子实体类
            album: JmAlbumDetail = client.get_album_detail(id)

# 下载本子封面图，保存为 cover.png （图片后缀可指定为jpg、webp等）
            client.download_album_cover(id, './cover.png')
            image_path = "./cover.png"
            yield event.image_result(image_path)
            id=str(id).strip()
            detail= client.get_album_detail(id)
            if not detail:
                  yield event.plain_result(MessageFormatter.format_error("not_found"))
                  return
            yield  event.plain_result(detail.title)
            if os.path.exists(image_path):
                 os.remove(image_path)
        elif command_type == "download":
            if len(args) < 3:
                    yield event.plain_result("请输入作品id：/jmcomic download [id]")
                    return
                    
            id = args[2]
            if not id.isdigit():
                    yield event.plain_result("作品ID必须是数字")
                    return
        album_id = id  
        album_folder = None
        pdf_file = None
        file_count = 0

        before_dirs = set([d.name for d in Path('.').iterdir() if d.is_dir()])

# 下载本子
        option = JmOption.default()
        download_album(album_id, option)

# 记录下载后的文件夹
        after_dirs = set([d.name for d in Path('.').iterdir() if d.is_dir()])

# 找出新创建的文件夹
        new_dirs = after_dirs - before_dirs

        if new_dirs:
               album_folder = Path(list(new_dirs)[0])
               pdf_filename = f"JM_{album_id}_{int(time.time())}.pdf"
               pdf_path_obj = Path(pdf_filename).resolve()
    
    # 1. 收集图片路径并排序（确保页码顺序正确）
    # 假设图片后缀是 .jpg 或 .png
               images = []
               extensions = ('.jpg', '.jpeg', '.png', '.webp')
    
    # 获取文件夹下所有图片并按文件名自然排序
               img_paths = [
                   str(f) for f in album_folder.rglob('*') 
                      if f.suffix.lower() in extensions
                             ]
               img_paths.sort() # 这一步很重要，防止乱序
    
               if img_paths:
        # 2. 转换为 PDF
                   with open(pdf_path_obj, "wb") as f:
                     f.write(img2pdf.convert(img_paths))
        
                   file_count = len(img_paths)
                   pdf_full_path = str(pdf_path_obj).replace("\\", "/")

        # 3. 构造发送组件
                   from astrbot.api.message_components import File, Plain
                   components = [
                        Comp.File(file=str(pdf_full_path), name=f"JM_{album_id}.pdf"),
                        
        ]
        
                   yield event.chain_result(components)
                   shutil.rmtree(album_folder)
                   os.remove(pdf_path_obj)