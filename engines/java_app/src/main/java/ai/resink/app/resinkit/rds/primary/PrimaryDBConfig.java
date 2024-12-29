// (C)2024 resink.ai
package ai.resink.app.resinkit.rds.primary;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import org.apache.ibatis.session.SqlSessionFactory;
import org.mybatis.spring.SqlSessionFactoryBean;
import org.mybatis.spring.SqlSessionTemplate;
import org.mybatis.spring.annotation.MapperScan;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;

import javax.sql.DataSource;

@Configuration
// @MapperScan("ai.resink.app.rds.primary.mapper")
@MapperScan(value = "ai.resink.app.resinkit.rds.primary.mapper", sqlSessionFactoryRef = "primarySqlSessionFactory")
public class PrimaryDBConfig {

    // ref:
    // https://docs.spring.io/spring-boot/docs/2.0.x/reference/html/howto-data-access.html
    // https://mdwgti16.github.io/spring%20boot/spring_boot_mybatis_multi/#

    @Bean
    @Primary
    @Qualifier("primaryHikariConfig")
    @ConfigurationProperties(prefix = "spring.datasource.primary")
    public HikariConfig primaryHikariConfig() {
        return new HikariConfig();
    }

    @Bean
    @Primary
    @Qualifier("primaryDataSource")
    public DataSource primaryDataSource() {
        return new HikariDataSource(primaryHikariConfig());
    }

    @Primary
    @Bean(name = "primarySqlSessionFactory")
    public SqlSessionFactory sqlSessionFactory(@Qualifier("primaryDataSource") DataSource dataSource) throws Exception {
        SqlSessionFactoryBean sqlSessionFactoryBean = new SqlSessionFactoryBean();
        sqlSessionFactoryBean.setDataSource(dataSource);
        return sqlSessionFactoryBean.getObject();
    }

    @Primary
    @Bean(name = "primarySqlSessionTemplate")
    public SqlSessionTemplate sqlSessionTemplate(
            @Qualifier("primarySqlSessionFactory") SqlSessionFactory sqlSessionFactory) {
        return new SqlSessionTemplate(sqlSessionFactory);
    }
}
