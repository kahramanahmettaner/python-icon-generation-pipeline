import openart_pipeline

if __name__ == "__main__":
    # Create the main tkinter window and start the app
    root = openart_pipeline.tk.Tk()
    app = openart_pipeline.OpenArtPipelineUI(root)
    root.mainloop()
