def main():
    files_in_current_dir = os.path.exists("output.avi")
    if not files_in_current_dir:
        resize_vid()
    screen_grabs = os.listdir("screengrab")
    if not len(screen_grabs):
        convert_vid_to_frames()
    best_grabs = get_best_images(screen_grabs)
    remove_all_files_bg(best_grabs)
    