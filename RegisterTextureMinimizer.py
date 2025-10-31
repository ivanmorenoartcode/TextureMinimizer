import unreal

tool_menus = unreal.ToolMenus.get()
main_menu = tool_menus.find_menu("LevelEditor.MainMenu")

if not main_menu:
    main_menu = tool_menus.extend_menu("LevelEditor.MainMenu")

custom_menu = main_menu.add_sub_menu("MyCustomSection", "My Custom Tools", "CustomTools", "Custom tools")

@unreal.uclass()
class ExecuteChangeTextureApp(unreal.ToolMenuEntryScript):
    @unreal.ufunction(override=True)
    def execute(self, context):
        widget_path = "/Script/Blutility.EditorUtilityWidgetBlueprint'/Game/TextureMinimizerTool/EUW_TextureMinimizer.EUW_TextureMinimizer'"
        widget_asset = unreal.EditorAssetLibrary.load_asset(widget_path)
        if not widget_asset:
            unreal.log_error(f"Could not find widget at: {widget_path}")
        elif not isinstance(widget_asset, unreal.EditorUtilityWidgetBlueprint):
            unreal.log_error(f"Asset at {widget_path} is not an Editor Utility Widget Blueprint.")
        else:
            subsystem = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
            subsystem.spawn_and_register_tab(widget_asset)
            unreal.log(f"Opening: {widget_path}")

script_object = ExecuteChangeTextureApp()
script_object.init_entry(
    owner_name=custom_menu.menu_name,
    menu=custom_menu.menu_name,
    section="",
    name="Texture Minimizer",
    label="Texture Minimizer",
    tool_tip="Open the Texture Minimizer tool"
)

script_object.register_menu_entry()
tool_menus.refresh_all_widgets()