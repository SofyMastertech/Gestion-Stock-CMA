import cProfile
import ui_manager

if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()
    ui_manager.MainWindow()  # Remplacez par l'appel principal de votre application
    profiler.disable()
    profiler.print_stats(sort='time')