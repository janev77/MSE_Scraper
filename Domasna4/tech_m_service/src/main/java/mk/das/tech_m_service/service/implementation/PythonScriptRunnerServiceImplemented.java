package mk.das.tech_m_service.service.implementation;

import mk.das.tech_m_service.service.PythonScriptRunnerService;
import mk.das.tech_m_service.web.controller.Tech_Analysis_Controller;
import org.springframework.core.io.ResourceLoader;
import org.springframework.stereotype.Service;

import java.io.*;
import java.time.LocalDateTime;
import java.util.ArrayList;

@Service
public class PythonScriptRunnerServiceImplemented implements PythonScriptRunnerService {

    private final ResourceLoader resourceLoader;

    public PythonScriptRunnerServiceImplemented(ResourceLoader resourceLoader) {
        this.resourceLoader = resourceLoader;
    }


    @Override
    public void run_script() {
        if (!Tech_Analysis_Controller.script_running_flag) {
            System.out.println("Starting Python script 'Tech Analysis' in background...");

            // Релативна патека до директориумот каде се наоѓа Python скриптата
            File workingDirectory = new File(System.getProperty("user.dir"), "/src/main/python");        //TODO Voa treba se smene ako frla error file not found


            // Проверка дали директориумот постои и е валиден
            if (!workingDirectory.exists() || !workingDirectory.isDirectory()) {
                throw new RuntimeException("Invalid directory: " + workingDirectory.getAbsolutePath());
            }

            String pythonPath = "python3";  //TODO change this if the python.exe file is not in default place

            File scriptFile = new File(workingDirectory, "Main.py");

            // Проверка дали Python скриптата постои
            if (!scriptFile.exists()) {
                throw new RuntimeException("Python script not found: " + scriptFile.getAbsolutePath());
            }

            // Креирај процес за извршување на Python скриптата
            ProcessBuilder processBuilder = new ProcessBuilder(pythonPath, scriptFile.getAbsolutePath());
            processBuilder.environment().put("PYTHONIOENCODING", "utf-8");
            processBuilder.redirectErrorStream(true);

            // Run the script in a new thread
            new Thread(() -> {
                ArrayList<String> log_list=new ArrayList<>();
                try {
                    // Стартувај ја скриптата во позадина
                    Process process;

                    try {
                        Tech_Analysis_Controller.script_running_flag=true;
                        process = processBuilder.start();

                        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                            String line;
                            while ((line = reader.readLine()) != null) {
                                log_list.add(line);
                            }
                        }


                    } catch (IOException e) {
                        throw new RuntimeException(e);
                    }
                    int exitCode = process.waitFor(); // Чека завршување на скриптата
                    if (exitCode == 0) {
                        System.out.println("Python script 'Tech Analysis' finished successfully.");
                        Tech_Analysis_Controller.script_last_run_time= LocalDateTime.now();

                    } else {
                        System.err.println("Python script 'Tech Analysis' exited with code: " + exitCode);

                        for (String s : log_list) {
                            System.out.println("PROCESS OUT:"+s);
                        }

                    }
                } catch (InterruptedException e) {
                    System.err.println("Error while waiting for Python script 'Tech Analysis' to finish: "
                            + e.getMessage());
                    Thread.currentThread().interrupt();
                } finally {
                    Tech_Analysis_Controller.script_running_flag=false;
                }
            }).start();


            System.out.println("Python script 'Tech Analysis' is running in the background...");
        }
    }
}