package ai.resink.app.resinkit;


import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class SwaggerConfig {

    @Bean
    public OpenAPI resinkitOpenAPI() {
        return new OpenAPI()
                .info(new Info().title("Resinkit API")
                        .description("Resinkit service API documentation")
                        .version("v0.0.1"));
    }
}