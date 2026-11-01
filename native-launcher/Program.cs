using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Text.RegularExpressions;

// Launch-only helper. Never changes aliases, vconf or installed applications.
class Program {
    [DllImport("libc.so.6")] static extern uint getuid();
    [DllImport("libc.so.6")] static extern void free(IntPtr p);
    [DllImport("libaul.so.0")] static extern int aul_launch_app_for_uid(string app, IntPtr bundle, uint uid);
    [DllImport("libaul.so.0")] static extern int aul_svc_get_appid_by_alias_appid_for_uid(string alias, out IntPtr target, uint uid);
    const string Dir = "/home/owner/share/tmp/sdk_tools/";
    static string LogPath;
    static void Log(string message) { File.AppendAllText(LogPath, message + "\n"); }
    static string Alias(string id) {
        IntPtr p; int rc = aul_svc_get_appid_by_alias_appid_for_uid(id, out p, 5001);
        try { if(rc < 0 || p == IntPtr.Zero) throw new Exception("Alias unavailable"); return Marshal.PtrToStringAnsi(p); }
        finally { if(p != IntPtr.Zero) free(p); }
    }
    static void Launch(string app) {
        int rc = aul_launch_app_for_uid(app, IntPtr.Zero, 5001);
        Log("LAUNCH_RC=" + rc);
        if(rc < 0) throw new Exception("Launch rejected");
    }
    static int Main(string[] args) {
        if(args.Length != 3 || !Regex.IsMatch(args[0], "\\A[a-f0-9]{32}\\z") ||
           (args[1] != "app" && args[1] != "settings") ||
           !Regex.IsMatch(args[2], "\\A[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\\z")) return 2;
        LogPath = Dir + "cf-ha-result-" + args[0] + ".txt";
        try { using(var f = new FileStream(Dir + "cf-ha-once-" + args[0], FileMode.CreateNew, FileAccess.Write)) {} }
        catch(IOException) { return 3; }
        try {
            if(getuid() != 901 || !File.ReadAllText("/etc/prd_info.ini").Contains("Version=T-NKMDEUC-2743.0;"))
                throw new Exception("Firmware/UID guard failed");
            if(Alias("org.tizen.app-selector") != "com.samsung.tv.app-selector")
                throw new Exception("Positive control failed");
            if(args[2] == "org.cleanframe.samsung-home" && Alias(args[2]) != "com.samsung.tv.csfs")
                throw new Exception("Samsung escape alias missing");
            if(args[1] == "settings") {
                Launch("org.tizen.tv-viewer");
                Launch("org.tizen.menu");
            } else Launch(args[2]);
            Log("CF_LAUNCH_ACCEPTED");
            return 0;
        } catch(Exception e) {
            Log("CF_LAUNCH_ERROR=" + e.Message);
            return 1;
        }
    }
}
