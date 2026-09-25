import com.google.gson.JsonParser;
import com.google.gson.JsonSyntaxException;
import com.google.gson.stream.JsonReader;
import com.google.gson.stream.MalformedJsonException;
import java.io.IOException;
import java.io.StringReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

/** Strict JSON syntax checker for resource files (uses the project's own Gson). */
public final class JsonCheck {

    public static void main(String[] args) throws IOException {
        int bad = 0;
        for (String arg : args) {
            Path path = Path.of(arg);
            try {
                String text = Files.readString(path, StandardCharsets.UTF_8);
                JsonReader reader = new JsonReader(new StringReader(text));
                reader.setLenient(false);
                JsonParser.parseReader(reader);
                if (reader.peek() != com.google.gson.stream.JsonToken.END_DOCUMENT) {
                    throw new JsonSyntaxException("trailing content after the root value");
                }
                System.out.println("  [OK]   " + path.getFileName());
            } catch (MalformedJsonException | JsonSyntaxException e) {
                bad++;
                System.out.println("  [FAIL] " + path.getFileName() + "  ->  " + e.getMessage());
                if (e instanceof MalformedJsonException) {
                    System.out.println("         line " + e.getMessage());
                }
            } catch (IOException e) {
                bad++;
                System.out.println("  [FAIL] " + path.getFileName() + "  ->  " + e);
            }
        }
        System.out.println(bad == 0 ? "JSON 全部合法" : ("JSON 非法文件数: " + bad));
        if (bad > 0) {
            System.exit(1);
        }
    }
}