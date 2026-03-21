from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp
from astrbot.api.event import MessageChain
from astrbot.api.message_components import File, Plain
import asyncio
from jmcomic import *
import os
import shutil
from pathlib import Path
import time
import img2pdf
import random
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
                "/jmcomic download [作品id]\n"
                "/jmcomic random \n"
                "/jmcomic tag [标签]\n"
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
            album: JmAlbumDetail = client.get_album_detail(id)
            client.download_album_cover(id, './cover.png')
            image_path = "./cover.png"
            yield event.image_result(image_path)
            id=str(id).strip()
            detail= client.get_album_detail(id)
            
            if not detail:
                  yield event.plain_result("未找到该作品信息")
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
            option = JmOption.default()
            download_album(album_id, option)
            after_dirs = set([d.name for d in Path('.').iterdir() if d.is_dir()])
            new_dirs = after_dirs - before_dirs
   
            if new_dirs:
               album_folder = Path(list(new_dirs)[0])
               pdf_filename = f"JM_{album_id}_{int(time.time())}.pdf"
               pdf_path_obj = Path(pdf_filename).resolve()
               images = []
               extensions = ('.jpg', '.jpeg', '.png', '.webp')
               img_paths = [
                   str(f) for f in album_folder.rglob('*') 
                      if f.suffix.lower() in extensions
                             ]
               img_paths.sort()
                
               if img_paths:
                   with open(pdf_path_obj, "wb") as f:
                     f.write(img2pdf.convert(img_paths))
                   file_count = len(img_paths)
                   pdf_full_path = str(pdf_path_obj).replace("\\", "/")
                   components = [
                        Comp.File(file=str(pdf_full_path), name=f"JM_{album_id}.pdf"),
        ]
        
                   yield event.chain_result(components)
                   shutil.rmtree(album_folder)
                   os.remove(pdf_path_obj)
        
        if command_type == "random":
             op = JmOption.default()
             cl = op.new_jm_client()
            
             def get_random_comic_from_category():
                  page = cl.categories_filter(
                  page=1, 
                 time=JmMagicConstants.TIME_WEEK,
                category=JmMagicConstants.CATEGORY_ALL,
                 order_by=JmMagicConstants.ORDER_BY_VIEW,
                   )
                  comic_list = list(page) 
                 
                  if not comic_list:
                     print("没有找到符合条件的本子")
                     return None, None
                  random_comic = random.choice(comic_list)
                  return random_comic
                 
             def get_random_comic_from_multiple_pages(max_page=3):
                  all_comics = []
                  current_page_num = 1 
                 
                  for page in cl.categories_filter_gen(
                     page=1,
                     time=JmMagicConstants.TIME_WEEK,
                     category=JmMagicConstants.CATEGORY_ALL,
                     order_by=JmMagicConstants.ORDER_BY_VIEW,
                          ):
                    all_comics.extend(list(page))
                              
                    if current_page_num >= max_page:
                         break
                    current_page_num += 1 
                              
                  if all_comics:
                     return random.choice(all_comics)
                  return None, None
             aid2, atitle2 = get_random_comic_from_multiple_pages(max_page=5)
             chain=[
                        Comp.Plain(f"随机选中的本子：ID: {aid2}, 标题: {atitle2}")
             ]
             yield event.chain_result(chain)
            
        if command_type == "tag":
            
            if len(args) < 3:
                yield event.plain_result("请输入标签：/jmcomic tag [标签]")
                return
            
            tag = args[2]
            option = JmOption.default()
            
            work_dir = os.getcwd()
            target_download_path = os.path.join(work_dir, 'downloads')
            os.makedirs(target_download_path, exist_ok=True)
            client = option.new_jm_client()
            print(f'\n[开始搜索] 标签: {tag}')
            aid_list = []
            
            for page_num in range(1, 11):
                page: JmSearchPage = client.search_tag(tag, page=page_num)
                for aid, atitle, tag_list in page.iter_id_title_tag():
                    aid_list.append((aid, atitle))
            print(f'[搜索完成] 共找到 {len(aid_list)} 个相册')
            
            if aid_list:
                # 随机选择一个相册
                random_album = random.choice(aid_list)
                aid, atitle = random_album
                print(f'[随机选中] AID: {aid}, 标题: {atitle}')
                print(f'[下载开始] 正在下载...')
                before_download = set(os.listdir(work_dir)) if os.path.exists(work_dir) else set()
                download_album([aid], option)
                print('[下载完成] 正在移动文件...')
                after_download = set(os.listdir(work_dir)) if os.path.exists(work_dir) else set()
                new_folders = after_download - before_download
                
                if new_folders:
                    for new_folder in new_folders:
                        src_path = os.path.join(work_dir, new_folder)
                        dst_path = os.path.join(target_download_path, new_folder)
                        
                        if os.path.isdir(src_path):
                            print(f'[移动文件] {new_folder}')
                           
                            if os.path.exists(dst_path):
                                shutil.rmtree(dst_path)
                            shutil.move(src_path, dst_path)
                            print(f'[成功] 已移动到 {dst_path}')
                            album_folder = Path(dst_path)
                            
                            if album_folder.exists():
                                pdf_filename = f"JM_{aid}_{int(time.time())}.pdf"
                                pdf_path_obj = Path(work_dir) / pdf_filename
                                extensions = ('.jpg', '.jpeg', '.png', '.webp')
                                img_paths = sorted([str(f) for f in album_folder.rglob('*') 
                                                  if f.suffix.lower() in extensions])
                                
                                if img_paths:
                                    with open(pdf_path_obj, "wb") as f:
                                        f.write(img2pdf.convert(img_paths))
                                    
                                    pdf_full_path = str(pdf_path_obj).replace("\\", "/")
                                    components = [
                                        Comp.File(file=str(pdf_full_path), name=f"JM_{aid}.pdf"),
                                    ]
                                    yield event.chain_result(components)
                                    shutil.rmtree(album_folder)
                                    os.remove(pdf_path_obj)
                else:
                    print('[警告] 未找到新增文件夹，文件可能下载到其他位置')
            else:
                print(f'[搜索结果] 未找到匹配 "{tag}" 的内容')
                yield event.plain_result(f'未找到匹配 "{tag}" 的内容')
