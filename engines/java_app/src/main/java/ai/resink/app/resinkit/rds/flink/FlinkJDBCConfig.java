// (C)2024 resink.ai
package ai.resink.app.resinkit.rds.flink;

import com.zaxxer.hikari.HikariConfig;
import org.apache.flink.table.jdbc.FlinkDataSource;
import org.apache.ibatis.session.SqlSessionFactory;
import org.mybatis.spring.SqlSessionFactoryBean;
import org.mybatis.spring.SqlSessionTemplate;
import org.mybatis.spring.annotation.MapperScan;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import javax.sql.DataSource;
import java.util.Properties;

@Configuration
@MapperScan(value = "ai.resink.app.resinkit.rds.flink.mapper", sqlSessionFactoryRef = "flinkSqlSessionFactory")
public class FlinkJDBCConfig {

    @Bean
    @Qualifier("flinkHikariConfig")
    @ConfigurationProperties(prefix = "spring.datasource.flink")
    public HikariConfig flinkHikariConfig() {
        HikariConfig config = new HikariConfig();
        config.addDataSourceProperty("readOnly", "false");
        config.setAutoCommit(true);
        config.setConnectionTestQuery("SELECT 1");
        return config;
    }

    @Bean
    @Qualifier("flinkDataSource")
    public DataSource flinkDataSource(@Qualifier("flinkHikariConfig") HikariConfig flinkHikariConfig) {
        return new FlinkDataSource(flinkHikariConfig.getJdbcUrl(), new Properties());
    }

    @Bean(name = "flinkSqlSessionFactory")
    public SqlSessionFactory sqlSessionFactory(@Qualifier("flinkDataSource") DataSource dataSource) throws Exception {
        SqlSessionFactoryBean sqlSessionFactoryBean = new SqlSessionFactoryBean();
        sqlSessionFactoryBean.setDataSource(dataSource);
        return sqlSessionFactoryBean.getObject();
    }

    @Bean(name = "flinkSqlSessionTemplate")
    public SqlSessionTemplate sqlSessionTemplate(@Qualifier("flinkSqlSessionFactory") SqlSessionFactory sqlSessionFactory) {
        return new SqlSessionTemplate(sqlSessionFactory);
    }
}
